import asyncio
import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
)

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Award specific badges and notify users.")
console = Console()

TARGET_BADGE_IDS = {"autor", "incomprendido", "insistente"}


async def notify_user(user, badges, tg_app, slack_app) -> bool:
    """Sends a notification to the user about their new badges."""
    badge_list_str = "\n".join([f"{b.icon} *{b.name}*: {b.description}" for b in badges])
    text = (
        f"¡Enhorabuena! Has ganado nuevos logros en CuñaoBot:\n\n"
        f"{badge_list_str}\n\n"
        f"Puedes ver todos tus logros en tu perfil web."
    )

    if user.platform == "telegram":
        if not tg_app:
            logger.error(f"Cannot notify Telegram user {user.id}: tg_app not initialized")
            return False
        try:
            await tg_app.bot.send_message(
                chat_id=user.id, text=text, parse_mode="Markdown"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to notify Telegram user {user.id}: {e}")
            return False
    elif user.platform == "slack":
        if not slack_app:
            logger.error(f"Cannot notify Slack user {user.id}: slack_app not initialized")
            return False
        try:
            # For Slack, we'd need to find the right token. 
            # This is a bit more complex so we'll try to use the default bot if configured
            # or skip if not easily found.
            from infrastructure.datastore.base import DatastoreRepository
            repo = DatastoreRepository("SlackBot")
            
            def _get_bot():
                query = repo.client.query(kind="SlackBot")
                return list(query.fetch(limit=1))
            
            bots = await asyncio.to_thread(_get_bot)
            if bots and "bot_token" in bots[0]:
                token = bots[0]["bot_token"]
                await slack_app.client.chat_postMessage(
                    token=token,
                    channel=user.id,
                    text=text.replace("*", ""), # Slack uses different bolding sometimes but chat_postMessage handles some markdown
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to notify Slack user {user.id}: {e}")
            return False
    return False


async def process_user(
    user, badge_service, progress, task, semaphore, stats, dry_run, tg_app, slack_app
) -> None:
    async with semaphore:
        try:
            # check_badges returns newly awarded Badge objects
            new_badges = await badge_service.check_badges(
                user.id, user.platform, save=not dry_run
            )

            if new_badges:
                # Filter for the ones the user specifically asked for if needed, 
                # but the user asked to "le de... y se les notifique", 
                # usually we notify for any new badge.
                
                # Check if any of the new badges are in our target list
                important_new_badges = [b for b in new_badges if b.id in TARGET_BADGE_IDS]
                
                stats["users_with_updates"] += 1
                stats["total_new_badges"] += len(new_badges)
                
                badge_names = ", ".join([b.name for b in new_badges])
                console.print(
                    f"  [green]+[/green] User {user.name or user.id} ({user.platform}) awarded: [bold]{badge_names}[/bold]"
                )

                if important_new_badges and not dry_run:
                    success = await notify_user(user, important_new_badges, tg_app, slack_app)
                    if success:
                        stats["notifications_sent"] += 1
                        console.print(f"    [blue]i[/blue] Notification sent to {user.id}")
                    else:
                        console.print(f"    [yellow]![/yellow] Could not notify {user.id}")
                elif important_new_badges and dry_run:
                    console.print(f"    [yellow]i[/yellow] Dry run: Would notify {user.id} about {len(important_new_badges)} badges")

        except Exception as e:
            console.print(f"  [red]![/red] Error processing user {user.id}: {e}")
        finally:
            progress.advance(task)


async def run_award_and_notify(dry_run: bool, concurrency: int) -> None:
    from services import user_service, badge_service
    
    tg_app = None
    slack_app = None
    
    if not dry_run:
        try:
            from tg import get_tg_application
            tg_app = get_tg_application()
            await tg_app.initialize()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize Telegram app: {e}[/yellow]")

        try:
            from slack.app import app as s_app
            slack_app = s_app
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize Slack app: {e}[/yellow]")

    users = await user_service.user_repo.load_all(ignore_gdpr=True)
    console.print(f"Found [bold]{len(users)}[/bold] users to process.")

    stats = {"total_new_badges": 0, "users_with_updates": 0, "notifications_sent": 0}
    semaphore = asyncio.Semaphore(concurrency)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing users...", total=len(users))

        tasks = [
            process_user(
                user, badge_service, progress, task, semaphore, stats, dry_run, tg_app, slack_app
            )
            for user in users
        ]
        await asyncio.gather(*tasks)

    if not dry_run and tg_app:
        await tg_app.shutdown()

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Users processed: {len(users)}")
    console.print(f"  Users with new badges: {stats['users_with_updates']}")
    console.print(f"  Total new badges awarded: {stats['total_new_badges']}")
    console.print(f"  Notifications sent: {stats['notifications_sent']}")

    if dry_run:
        console.print("\n[yellow]No changes were saved (Dry Run).[/yellow]")
    else:
        console.print("\n[green]Task completed successfully.[/green]")


@app.command()
def main(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Do not save changes or send notifications.")
    ] = False,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", help="Number of concurrent users to process.")
    ] = 10,
) -> None:
    """
    Recalculate badges and notify users about specific achievements.
    """
    try:
        asyncio.run(run_award_and_notify(dry_run, concurrency))
    except Exception as e:
        console.print(f"[red]Error during execution:[/red] {e}")
        # raise e # For debugging
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
