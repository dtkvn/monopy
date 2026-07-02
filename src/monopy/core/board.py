from dataclasses import dataclass
from enum import Enum, auto


class SpaceType(Enum):
    GO = auto()
    PROPERTY = auto()
    RAILROAD = auto()
    UTILITY = auto()
    CHANCE = auto()
    COMMUNITY_CHEST = auto()
    TAX = auto()
    JAIL = auto()
    GO_TO_JAIL = auto()
    FREE_PARKING = auto()


@dataclass
class Space:
    index: int
    name: str
    space_type: SpaceType
    price: int = 0
    rent: list[int] | None = None
    color_group: str | None = None
    owner_id: str | None = None
    houses: int = 0  # Number of houses (0-5)

    def __post_init__(self):
        if self.rent is None:
            self.rent = [0] * 6


class Board:
    TOTAL_SPACES = 40

    def __init__(self):
        self.spaces: list[Space] = self._initialize_board()

    def _initialize_board(self) -> list[Space]:
        """Generates the layout of the standard Monopoly board."""
        return [
            Space(0, "Go", SpaceType.GO),
            Space(
                1,
                "Mediterranean Avenue",
                SpaceType.PROPERTY,
                price=60,
                rent=[2, 10, 30, 90, 160, 250],
                color_group="brown",
            ),
            Space(2, "Community Chest", SpaceType.COMMUNITY_CHEST),
            Space(
                3,
                "Baltic Avenue",
                SpaceType.PROPERTY,
                price=60,
                rent=[4, 20, 60, 180, 320, 450],
                color_group="brown",
            ),
            Space(4, "Income Tax", SpaceType.TAX, price=200),
            Space(
                5,
                "Reading Railroad",
                SpaceType.RAILROAD,
                price=200,
                rent=[25, 50, 100, 200],
            ),
            Space(
                6,
                "Oriental Avenue",
                SpaceType.PROPERTY,
                price=100,
                rent=[6, 30, 90, 270, 400, 550],
                color_group="light_blue",
            ),
            Space(7, "Chance", SpaceType.CHANCE),
            Space(
                8,
                "Vermont Avenue",
                SpaceType.PROPERTY,
                price=100,
                rent=[6, 30, 90, 270, 400, 550],
                color_group="light_blue",
            ),
            Space(
                9,
                "Connecticut Avenue",
                SpaceType.PROPERTY,
                price=120,
                rent=[8, 40, 100, 300, 450, 600],
                color_group="light_blue",
            ),
            Space(10, "Jail / Just Visiting", SpaceType.JAIL),
            Space(
                11,
                "St. Charles Place",
                SpaceType.PROPERTY,
                price=140,
                rent=[10, 50, 150, 450, 625, 750],
                color_group="pink",
            ),
            Space(12, "Electric Company", SpaceType.UTILITY, price=150),
            Space(
                13,
                "States Avenue",
                SpaceType.PROPERTY,
                price=140,
                rent=[10, 50, 150, 450, 625, 750],
                color_group="pink",
            ),
            Space(
                14,
                "Virginia Avenue",
                SpaceType.PROPERTY,
                price=160,
                rent=[12, 60, 180, 500, 700, 900],
                color_group="pink",
            ),
            Space(
                15,
                "Pennsylvania Railroad",
                SpaceType.RAILROAD,
                price=200,
                rent=[25, 50, 100, 200],
            ),
            Space(
                16,
                "St. James Place",
                SpaceType.PROPERTY,
                price=180,
                rent=[14, 70, 200, 550, 750, 950],
                color_group="orange",
            ),
            Space(17, "Community Chest", SpaceType.COMMUNITY_CHEST),
            Space(
                18,
                "Tennessee Avenue",
                SpaceType.PROPERTY,
                price=180,
                rent=[14, 70, 200, 550, 750, 950],
                color_group="orange",
            ),
            Space(
                19,
                "New York Avenue",
                SpaceType.PROPERTY,
                price=200,
                rent=[16, 80, 220, 600, 800, 1000],
                color_group="orange",
            ),
            Space(20, "Free Parking", SpaceType.FREE_PARKING),
            Space(
                21,
                "Kentucky Avenue",
                SpaceType.PROPERTY,
                price=220,
                rent=[18, 90, 250, 700, 875, 1050],
                color_group="red",
            ),
            Space(22, "Chance", SpaceType.CHANCE),
            Space(
                23,
                "Indiana Avenue",
                SpaceType.PROPERTY,
                price=220,
                rent=[18, 90, 250, 700, 875, 1050],
                color_group="red",
            ),
            Space(
                24,
                "Illinois Avenue",
                SpaceType.PROPERTY,
                price=240,
                rent=[20, 100, 300, 750, 925, 1100],
                color_group="red",
            ),
            Space(
                25,
                "B. & O. Railroad",
                SpaceType.RAILROAD,
                price=200,
                rent=[25, 50, 100, 200],
            ),
            Space(
                26,
                "Atlantic Avenue",
                SpaceType.PROPERTY,
                price=260,
                rent=[22, 110, 330, 800, 975, 1150],
                color_group="yellow",
            ),
            Space(
                27,
                "Ventnor Avenue",
                SpaceType.PROPERTY,
                price=260,
                rent=[22, 110, 330, 800, 975, 1150],
                color_group="yellow",
            ),
            Space(28, "Water Works", SpaceType.UTILITY, price=150),
            Space(
                29,
                "Marvin Gardens",
                SpaceType.PROPERTY,
                price=280,
                rent=[24, 120, 360, 850, 1025, 1200],
                color_group="yellow",
            ),
            Space(30, "Go To Jail", SpaceType.GO_TO_JAIL),
            Space(
                31,
                "Pacific Avenue",
                SpaceType.PROPERTY,
                price=300,
                rent=[26, 130, 390, 900, 1100, 1275],
                color_group="green",
            ),
            Space(
                32,
                "North Carolina Avenue",
                SpaceType.PROPERTY,
                price=300,
                rent=[26, 130, 390, 900, 1100, 1275],
                color_group="green",
            ),
            Space(33, "Community Chest", SpaceType.COMMUNITY_CHEST),
            Space(
                34,
                "Pennsylvania Avenue",
                SpaceType.PROPERTY,
                price=320,
                rent=[28, 150, 450, 1000, 1200, 1400],
                color_group="green",
            ),
            Space(
                35,
                "Short Line Railroad",
                SpaceType.RAILROAD,
                price=200,
                rent=[25, 50, 100, 200],
            ),
            Space(36, "Chance", SpaceType.CHANCE),
            Space(
                37,
                "Park Place",
                SpaceType.PROPERTY,
                price=350,
                rent=[35, 175, 500, 1100, 1300, 1500],
                color_group="dark_blue",
            ),
            Space(38, "Luxury Tax", SpaceType.TAX, price=100),
            Space(
                39,
                "Boardwalk",
                SpaceType.PROPERTY,
                price=400,
                rent=[50, 200, 600, 1400, 1700, 2000],
                color_group="dark_blue",
            ),
        ]

    def get_space(self, index: int) -> Space:
        return self.spaces[index % self.TOTAL_SPACES]
