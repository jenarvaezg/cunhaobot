import asyncio
import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

# Configure logging to be less verbose during script execution
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Retroactively recalculate and award badges to all users.")
console = Console()


async def process_user(
    user, badge_service, progress, task, semaphore, stats, dry_run: bool
) -> None:
    async with semaphore:
        try:
            # check_badges returns newly awarded Badge objects
            new_badges = await badge_service.check_badges(user.id, user.platform)

            if new_badges:
                stats["users_with_updates"] += 1
                stats["total_new_badges"] += len(new_badges)
                badge_names = ", ".join([b.name for b in new_badges])
                console.print(
                    f"  [green]+[/green] User {user.name or user.id} ({user.platform}) awarded: [bold]{badge_names}[/bold]"
                )
        except Exception as e:
            console.print(f"  [red]![/red] Error processing user {user.id}: {e}")
        finally:
            progress.advance(task)


async def process_users(dry_run: bool, concurrency: int) -> None:
    from services import user_service, badge_service
    from unittest.mock import patch

    users = user_service.user_repo.load_all(ignore_gdpr=True)
    console.print(f"Found [bold]{len(users)}[/bold] users to process.")

    stats = {"total_new_badges": 0, "users_with_updates": 0}
    semaphore = asyncio.Semaphore(concurrency)

    if dry_run:
        console.print(
            "[yellow]DRY RUN MODE: No changes will be saved to the database.[/yellow]"
        )

    # If dry run, we patch the save_user method to do nothing
    # We patch it in UserService because BadgeService uses user_service instance
    with (
        patch("services.user_service.UserService.save_user")
        if dry_run
        else patch("services.badge_service.BadgeService.get_badge_info")
    ):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Recalculating badges...", total=len(users))

            tasks = [
                process_user(
                    user, badge_service, progress, task, semaphore, stats, dry_run
                )
                for user in users
            ]
            await asyncio.gather(*tasks)

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Users processed: {len(users)}")
    console.print(f"  Users with new badges: {stats['users_with_updates']}")
    console.print(f"  Total new badges awarded: {stats['total_new_badges']}")

    if dry_run:
        console.print("\n[yellow]No changes were saved (Dry Run).[/yellow]")
    else:
        console.print("\n[green]All badges have been successfully synchronized.[/green]")


@app.command()
def recalculate(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Do not save changes to the database.")
    ] = False,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", help="Number of concurrent users to process.")
    ] = 10,
) -> None:
    """
    Recalculate badges for all users based on their current stats and history.
    """
    try:
        asyncio.run(process_users(dry_run, concurrency))
    except Exception as e:
        console.print(f"[red]Error during execution:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
