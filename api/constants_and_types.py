from __future__ import annotations

from enum import Enum, StrEnum
from typing import Callable, List, Tuple

from pydantic import BaseModel

NUM_OPPONENTS = 5

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

RANK_VALUES = {rank: i + 2 for i, rank in enumerate(RANKS)}

HAND_NAMES = [
    "High Card",
    "Pair",
    "Two Pair",
    "Three of a Kind",
    "Straight",
    "Flush",
    "Full House",
    "Four of a Kind",
    "Straight Flush",
]


class Action(StrEnum):
    CHECK = "check"
    BET = "bet"
    CALL = "call"
    FOLD = "fold"


class ActionResponse(BaseModel):
    action: Action
    amount: int


class Suit(Enum):
    """Represent the four suits in a standard deck."""

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


Card = Tuple[int, Suit]
Hand = List[Card]


class Player(BaseModel):
    name: str
    chips: int
    hand: Hand
    action_func: Callable[[Player, int, int], ActionResponse]

    def __hash__(self):
        """Make Player hashable so it can be used in sets and as dict keys."""
        return hash(self.name)


def hand_to_string(hand: Hand) -> str:
    """Convert hand to readable string."""
    return " ".join(f"{RANKS[rank - 2]}{suit.value}" for rank, suit in hand)
