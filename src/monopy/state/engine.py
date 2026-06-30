import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from monopy.core.board import Board, Space, SpaceType

if TYPE_CHECKING:
    from monopy.core.player import Player


@dataclass
class TurnResult:
    player_name: str
    dice_roll: int
    was_doubles: bool
    passed_go: bool
    landed_space: Space
    action_taken: str
    rent_paid: int = 0
    card_drawn: str | None = None
    error_message: str | None = None


def calculate_rent(space: Space, board: Board, dice_roll: int) -> int:
    """Calculates rent based on standard Monopoly rules.

    Handles property monopoly, railroads, and utilities.
    """
    if not space.owner_id:
        return 0

    # Ensure rent list exists
    if space.rent is None:
        return 0

    if space.space_type == SpaceType.PROPERTY:
        # Check color group monopoly
        group_spaces = [s for s in board.spaces if s.color_group == space.color_group]
        has_monopoly = all(s.owner_id == space.owner_id for s in group_spaces)
        if has_monopoly:
            return space.rent[0] * 2
        return space.rent[0]

    elif space.space_type == SpaceType.RAILROAD:
        # Count owned railroads
        railroad_indices = {5, 15, 25, 35}
        owned_count = sum(
            1
            for s in board.spaces
            if s.index in railroad_indices and s.owner_id == space.owner_id
        )
        idx = max(0, min(owned_count - 1, 3))
        return space.rent[idx]

    elif space.space_type == SpaceType.UTILITY:
        # Count owned utilities
        utility_indices = {12, 28}
        owned_count = sum(
            1
            for s in board.spaces
            if s.index in utility_indices and s.owner_id == space.owner_id
        )
        multiplier = 10 if owned_count == 2 else 4
        return multiplier * dice_roll

    return 0


def process_player_turn(player: Player, d1: int, d2: int, board: Board) -> TurnResult:
    """Executes a full turn phase and handles consecutive doubles tracking."""
    total_roll = d1 + d2
    was_doubles = d1 == d2

    # 1. Handle Jail Breakout attempts first
    if player.in_jail:
        if was_doubles:
            player.in_jail = False
            player.jail_turns = 0
            # Getting out on doubles doesn't grant an extra roll
            player.consecutive_doubles = 0
        else:
            player.jail_turns += 1
            if player.jail_turns >= 3:
                player.adjust_balance(-50)
                player.in_jail = False
                player.jail_turns = 0
            else:
                return TurnResult(
                    player_name=player.name,
                    dice_roll=total_roll,
                    was_doubles=was_doubles,
                    passed_go=False,
                    landed_space=board.get_space(player.position),
                    action_taken="Stayed in Jail (Did not roll doubles)",
                )

    # 2. Track Doubles for active players out of Jail
    if was_doubles:
        player.consecutive_doubles += 1
        if player.consecutive_doubles >= 3:
            player.send_to_jail()
            return TurnResult(
                player_name=player.name,
                dice_roll=total_roll,
                was_doubles=was_doubles,
                passed_go=False,
                landed_space=board.get_space(player.position),
                action_taken="🚨 Sent to Jail for rolling 3 consecutive doubles!",
            )
    else:
        player.consecutive_doubles = 0

    # 3. Normal Movement & Tile Assessment
    passed_go = player.move(total_roll)
    if passed_go:
        player.adjust_balance(200)

    space = board.get_space(player.position)
    action = f"Landed on {space.name}."
    rent_paid = 0
    card_drawn_text = None

    # Handle Special Tile Interactions
    if space.space_type == SpaceType.GO_TO_JAIL:
        player.send_to_jail()
        action = "Sent directly to Jail!"
    elif space.space_type == SpaceType.TAX:
        tax_amount = 200 if space.index == 4 else 100
        player.adjust_balance(-tax_amount)
        action = f"Paid {space.name} fee of ${tax_amount}."
    elif space.space_type in {
        SpaceType.PROPERTY,
        SpaceType.RAILROAD,
        SpaceType.UTILITY,
    }:
        if space.owner_id and space.owner_id != player.id:
            rent_paid = calculate_rent(space, board, total_roll)
            player.adjust_balance(-rent_paid)
            action = f"Paid ${rent_paid} rent to Owner {space.owner_id}."
        elif space.owner_id is None:
            action = f"Available for purchase for ${space.price}."
    elif space.space_type in {SpaceType.CHANCE, SpaceType.COMMUNITY_CHEST}:
        # Draw Card
        if space.space_type == SpaceType.CHANCE:
            cards = [
                ("Advance to Go (Collect $200)", "go"),
                ("Advance to Illinois Avenue.", "illinois"),
                ("Advance to St. Charles Place.", "charles"),
                ("Bank pays you dividend of $50.", "dividend"),
                ("Go directly to Jail.", "jail"),
                ("Pay speeding fine of $15.", "speeding"),
                ("Your building loan matures. Collect $150.", "loan"),
                ("You inherit $100.", "inherit"),
            ]
        else:
            cards = [
                ("Advance to Go (Collect $200)", "go"),
                ("Bank error in your favor. Collect $200.", "bank_error"),
                ("Doctor's fees. Pay $50.", "doctor"),
                ("From sale of stock you get $50.", "stock"),
                ("Go directly to Jail.", "jail"),
                ("Holiday fund matures. Receive $100.", "holiday"),
                ("Income tax refund. Collect $20.", "refund"),
                ("Life insurance matures. Collect $100.", "insurance"),
                ("Pay hospital fees of $100.", "hospital"),
                ("Pay school fees of $50.", "school"),
            ]

        card_title, card_id = random.choice(cards)
        card_drawn_text = card_title
        action = f"Drew {space.space_type.name}: '{card_title}'."

        # Apply Card Effects
        if card_id == "go":
            player.position = 0
            player.adjust_balance(200)
        elif card_id == "illinois":
            old_pos = player.position
            player.position = 24
            if player.position < old_pos:
                player.adjust_balance(200)
                passed_go = True
            space = board.get_space(player.position)
        elif card_id == "charles":
            old_pos = player.position
            player.position = 11
            if player.position < old_pos:
                player.adjust_balance(200)
                passed_go = True
            space = board.get_space(player.position)
        elif card_id == "dividend":
            player.adjust_balance(50)
        elif card_id == "jail":
            player.send_to_jail()
            space = board.get_space(player.position)
            action += " Sent directly to Jail!"
        elif card_id == "speeding":
            player.adjust_balance(-15)
        elif card_id == "loan":
            player.adjust_balance(150)
        elif card_id == "inherit":
            player.adjust_balance(100)
        elif card_id == "bank_error":
            player.adjust_balance(200)
        elif card_id == "doctor":
            player.adjust_balance(-50)
        elif card_id == "stock":
            player.adjust_balance(50)
        elif card_id == "holiday":
            player.adjust_balance(100)
        elif card_id == "refund":
            player.adjust_balance(20)
        elif card_id == "insurance":
            player.adjust_balance(100)
        elif card_id == "hospital":
            player.adjust_balance(-100)
        elif card_id == "school":
            player.adjust_balance(-50)

        # Re-assess if moved to a property via card
        if card_id in {"illinois", "charles"}:
            if space.owner_id and space.owner_id != player.id:
                rent_paid = calculate_rent(space, board, total_roll)
                player.adjust_balance(-rent_paid)
                action += f" Paid ${rent_paid} rent to Owner {space.owner_id}."
            elif space.owner_id is None:
                action += f" Available for purchase for ${space.price}."

    return TurnResult(
        player_name=player.name,
        dice_roll=total_roll,
        was_doubles=was_doubles,
        passed_go=passed_go,
        landed_space=space,
        action_taken=action,
        rent_paid=rent_paid,
        card_drawn=card_drawn_text,
    )
