from monopy.core.board import Board, SpaceType
from monopy.core.player import Player
from monopy.state.engine import TurnResult, process_player_turn


class GameManager:
    def __init__(self, player_definitions: list[dict[str, str]]):
        self.board = Board()
        self.players: list[Player] = [
            Player(id=p["id"], name=p["name"]) for p in player_definitions
        ]
        self.current_player_index = 0
        self.extra_turn_earned = False
        self.phase = "ROLL"  # ROLL, BUY_DECISION, JAIL_DECISION, END_TURN, GAME_OVER
        self.last_roll = None
        self.history: list[str] = ["Game started!"]
        self.winner_name: str | None = None

        # Check if first player is in jail
        if self.current_player.in_jail:
            self.phase = "JAIL_DECISION"

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def roll_dice(self, d1: int, d2: int) -> TurnResult:
        """Executes a roll and moves the player. Handles phase transitions."""
        if self.phase not in ("ROLL", "JAIL_DECISION"):
            return TurnResult(
                player_name=self.current_player.name,
                dice_roll=d1 + d2,
                was_doubles=d1 == d2,
                passed_go=False,
                landed_space=self.board.get_space(self.current_player.position),
                action_taken="Cannot roll in this phase.",
                error_message="Invalid action for current phase.",
            )

        player = self.current_player
        result = process_player_turn(player, d1, d2, self.board)
        self.last_roll = (d1, d2)

        # Log event
        self.history.append(
            f"🎲 {player.name} rolled {d1} & {d2}. {result.action_taken}"
        )

        # Determine next phase
        if player.in_jail:
            self.phase = "END_TURN"
            self.extra_turn_earned = False
        else:
            if result.was_doubles:
                self.extra_turn_earned = True
            else:
                self.extra_turn_earned = False

            # Check landing space for buy decision
            space = result.landed_space
            is_purchasable = space.space_type in (
                SpaceType.PROPERTY,
                SpaceType.RAILROAD,
                SpaceType.UTILITY,
            )
            if is_purchasable and space.owner_id is None:
                self.phase = "BUY_DECISION"
            else:
                self.phase = "END_TURN"

        # Check if player went bankrupt from tax or rent
        self._check_bankruptcies()

        return result

    def buy_current_property(self) -> bool:
        """Attempts to purchase the property the current player is landing on."""
        if self.phase != "BUY_DECISION":
            return False

        player = self.current_player
        space = self.board.get_space(player.position)

        if space.owner_id is not None:
            return False

        if player.balance < space.price:
            self.history.append(f"❌ {player.name} couldn't afford {space.name}.")
            return False

        # Transact
        player.adjust_balance(-space.price)
        space.owner_id = player.id
        player.properties.add(space.index)

        self.history.append(f"🏠 {player.name} bought {space.name} for ${space.price}.")
        self.phase = "END_TURN"
        return True

    def pass_current_property(self) -> bool:
        """Declines purchasing the property the current player is landing on."""
        if self.phase != "BUY_DECISION":
            return False

        player = self.current_player
        space = self.board.get_space(player.position)

        self.history.append(f"🏳️ {player.name} passed on buying {space.name}.")
        self.phase = "END_TURN"
        return True

    def pay_jail_fine(self) -> bool:
        """Pays $50 fine to escape jail."""
        player = self.current_player
        if not player.in_jail or player.balance < 50:
            return False

        player.adjust_balance(-50)
        player.in_jail = False
        player.jail_turns = 0
        self.phase = "ROLL"
        self.history.append(f"🔓 {player.name} paid $50 fine to get out of Jail.")
        return True

    def end_turn(self) -> bool:
        """Ends the current player's turn and advances to the next player."""
        if self.phase != "END_TURN":
            return False

        # Advance player
        if not self.extra_turn_earned:
            active_players = [p for p in self.players if p.balance >= 0]
            if not active_players:
                self.phase = "GAME_OVER"
                return True

            # Find next active player
            while True:
                self.current_player_index = (self.current_player_index + 1) % len(
                    self.players
                )
                if self.current_player.balance >= 0:
                    break
        else:
            self.history.append(
                f"🔄 Doubles! {self.current_player.name} gets another turn."
            )

        self.extra_turn_earned = False

        # Setup next turn phase
        if self.current_player.in_jail:
            self.phase = "JAIL_DECISION"
        else:
            self.phase = "ROLL"

        self.history.append(f"⏱️ It is now {self.current_player.name}'s turn.")
        return True

    def _check_bankruptcies(self):
        """Checks if players are bankrupt (balance < 0) and releases assets."""
        for player in self.players:
            if player.balance < 0 and len(player.properties) > 0:
                # Bankrupt: Release all properties
                released = []
                for space in self.board.spaces:
                    if space.owner_id == player.id:
                        space.owner_id = None
                        released.append(space.name)
                player.properties.clear()
                self.history.append(
                    f"💀 {player.name} has gone Bankrupt! "
                    f"Released properties: {', '.join(released)}"
                )
            elif player.balance < 0:
                self.history.append(f"💀 {player.name} has gone Bankrupt!")

        # Check winner
        active_players = [p for p in self.players if p.balance >= 0]
        if len(active_players) == 1 and len(self.players) > 1:
            self.phase = "GAME_OVER"
            self.winner_name = active_players[0].name
            self.history.append(f"🏆 {self.winner_name} wins the game!")

    def play_turn(self, d1: int, d2: int) -> TurnResult:
        """Compatibility method for CLI. Automatically handles buy decision."""
        self.phase = "ROLL"
        res = self.roll_dice(d1, d2)
        if self.phase == "BUY_DECISION":
            self.buy_current_property()
        return res

    def advance_turn(self):
        """Compatibility method for CLI. Automatically ends turn."""
        self.phase = "END_TURN"
        self.end_turn()
