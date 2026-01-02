import asyncio
import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configure logging to be less verbose during script execution
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Retroactively recalculate and award badges to all users.")
console = Console()


async def process_users(dry_run: bool) -> None:
    # We import inside the function to ensure the environment is set up if needed
    # and to avoid top-level async issues or circular imports
    from services import user_service, badge_service
    from unittest.mock import patch

    users = user_service.user_repo.load_all(ignore_gdpr=True)
    console.print(f"Found [bold]{len(users)}[/bold] users to process.")

    total_new_badges = 0
    users_with_updates = 0

    if dry_run:
        console.print("[yellow]DRY RUN MODE: No changes will be saved to the database.[/yellow]")

    # If dry run, we patch the save_user method to do nothing
    with patch("services.user_service.UserService.save_user") if dry_run else patch("services.badge_service.BadgeService.get_badge_info") as p:
        # In non-dry run, the second patch is just a no-op placeholder
        if dry_run:
            logger.info("Patching save_user for dry run")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Recalculating badges...", total=len(users))

            for user in users:
                progress.update(task, description=f"Processing {user.name or user.id}...")
                
                # We use the master user ID if linked, but check_badges already handles that
                # by calling get_user internally.
                new_badges = await badge_service.check_badges(user.id, user.platform)
                
                if new_badges:
                    users_with_updates += 1
                    total_new_badges += len(new_badges)
                    badge_names = ", ".join([b.name for b in new_badges])
                    console.print(f"  [green]+[/green] User {user.name or user.id} ({user.platform}) awarded: [bold]{badge_names}[/bold]")
                
                progress.advance(task)

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Users processed: {len(users)}")
    console.print(f"  Users with new badges: {users_with_updates}")
    console.print(f"  Total new badges awarded: {total_new_badges}")
    
    if dry_run:
        console.print("\n[yellow]No changes were saved (Dry Run).[/yellow]")
    else:
        console.print("\n[green]All badges have been successfully synchronized.[/green]")


@app.command()
def recalculate(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Do not save changes to the database.")
    ] = False,
) -> None:
    """
    Recalculate badges for all users based on their current stats and history.
    """
    try:
        asyncio.run(process_users(dry_run))
    except Exception as e:
        console.print(f"[red]Error during execution:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
