"""Command-line interface for monopy."""

import random

import typer

from monopy import __version__
from monopy.core.board import Board
from monopy.core.player import Player
from monopy.state.engine import process_player_turn
from monopy.state.game_manager import GameManager

app = typer.Typer(
    name="monopy",
    help="A Python package",
    add_completion=False,
)

BOARD = Board()
PLAYERS = {
    "1": Player(id="1", name="Kevin", balance=1500),
    "2": Player(id="2", name="Tyrone", balance=1500),
}


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"monopy version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """A Python package."""


@app.command()
def hello(
    name: str = typer.Argument("World", help="Name to greet"),
) -> None:
    """Say hello to someone."""
    typer.echo(f"Hello, {name}!")


@app.command()
def roll(
    player_id: str = typer.Argument(..., help="Player ID"),
    d1: int = typer.Option(..., min=1, max=6),
    d2: int = typer.Option(..., min=1, max=6),
):
    player = PLAYERS.get(player_id)
    if not player:
        typer.secho("❌ Player not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Call the updated engine
    result = process_player_turn(player, d1, d2, BOARD)

    # Display UI elements cleanly based on the state results
    typer.echo(
        f"🎲 {result.player_name} rolled {d1} & {d2} (Total: {result.dice_roll})"
    )
    if result.was_doubles:
        typer.secho("🔥 DOUBLES!", fg=typer.colors.YELLOW, bold=True)

    if result.passed_go:
        typer.secho("✨ Passed GO! Collected $200.", fg=typer.colors.CYAN)

    typer.secho(f"📍 Location: {result.landed_space.name}", fg=typer.colors.GREEN)
    typer.echo(f"📋 Action: {result.action_taken}")
    typer.echo(f"💰 Wallet: ${player.balance}")


@app.command()
def start():
    typer.secho("Welcome to Monopy CLI!", fg=typer.colors.CYAN, bold=True)

    game = GameManager(
        [
            {"id": "1", "name": "Kevin"},
            {"id": "2", "name": "Alice"},
        ]
    )

    playing = True
    while playing:
        player = game.current_player
        msg = (
            f"\n{player.name}'s turn "
            f"(Balance: ${player.balance}, Position: {player.position})"
        )
        typer.secho(
            msg,
            fg=typer.colors.MAGENTA,
        )

        action = typer.prompt(
            "Press Enter to roll the dice (or type 'q' to exit)",
            default="",
            show_default=False,
        )
        if action.lower() == "q":
            playing = False
            continue

        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)

        result = game.play_turn(d1, d2)

        typer.echo(f"Rolled: {d1} + {d2} = {result.dice_roll}")
        if result.was_doubles:
            typer.secho("DOUBLES!", fg=typer.colors.YELLOW, bold=True)

        typer.echo(f"Action: {result.action_taken}")
        typer.echo(f"New Balance: ${player.balance}")

        if game.extra_turn_earned:
            typer.secho(
                f"Doubles rule triggered! {player.name} gets to roll again.",
                fg=typer.colors.YELLOW,
            )

        game.advance_turn()

    typer.echo("Game session closed. Thanks for playing!")


if __name__ == "__main__":
    app()
