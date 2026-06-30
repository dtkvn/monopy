from dataclasses import dataclass, field


@dataclass
class Player:
    id: str
    name: str
    balance: int = 1500
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    consecutive_doubles: int = 0
    properties: set[int] = field(default_factory=set)  # Tracks indices of owned spaces

    def move(self, steps: int) -> bool:
        """
        Moves the player a number of steps around the circular board.
        Returns True if the player passed GO, otherwise False.
        """
        if self.in_jail:
            return False

        old_position = self.position
        self.position = (self.position + steps) % 40

        # If the new position index dropped below the old index, we circled around Go
        return self.position < old_position

    def adjust_balance(self, amount: int) -> bool:
        """Modifies player funds. Returns False if player cannot afford the expense."""
        if self.balance + amount < 0:
            return False
        self.balance += amount
        return True

    def send_to_jail(self):
        self.position = 10  # Standard index for Jail
        self.in_jail = True
        self.jail_turns = 0
        self.consecutive_doubles = 0
