from __future__ import annotations

from enum import Enum, StrEnum
from typing import Callable, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

STARTING_CHIPS = 1000

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
    CALL = "call"
    FOLD = "fold"
    RAISE = "raise"


class BettingRound(StrEnum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"

    def rank(self) -> int:
        return {self.PRE_FLOP: 0, self.FLOP: 1, self.TURN: 2, self.RIVER: 3}[self]


class ActionResponse(BaseModel):
    action: Action
    amount: int
    actual_amount_contributed: int = 0  # The actual amount the player contributed to the pot


class BettingRoundResult(BaseModel):
    round_number: int
    betting_round_type: BettingRound
    players_actions: Dict[Player, ActionResponse]
    starting_pot: int
    final_pot: int
    community_cards: List[Card]
    active_players: List[Player]


class GameResult(BaseModel):
    """Result of a single poker game."""

    winner: str
    rounds_played: int
    final_rankings: List[Player]
    eliminated_players: List[Player]
    betting_rounds: List[BettingRoundResult]


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
    action_func: Callable[[Player, int, int, List[Card], BettingRound], ActionResponse]

    def __hash__(self):
        """Make Player hashable so it can be used in sets and as dict keys."""
        return hash(self.name)


def hand_to_string(hand: Hand) -> str:
    """Convert hand to readable string."""
    return " ".join(f"{RANKS[rank - 2]}{suit.value}" for rank, suit in hand)


class CheckOrRaise(BaseModel):
    action: Literal["check", "raise"]
    amount: Optional[int] = Field(None, description="The amount to raise if the action is raise. Otherwise, None.")


class CallFoldOrRaise(BaseModel):
    action: Literal["call", "fold", "raise"]
    amount: Optional[int] = Field(None, description="The amount to raise if the action is raise. Otherwise, None.")


class CheckOrRaiseWithReasoning(BaseModel):
    reasoning: str = Field(
        ...,
        description="Think step by step (reasoning about bet sizing math, GTO play, etc.), and decide what action to take maximizes your expected value.",
    )
    action: Literal["check", "raise"]
    amount: Optional[int] = Field(None, description="The amount to raise if the action is raise. Otherwise, None.")


class CallFoldOrRaiseWithReasoning(BaseModel):
    reasoning: str = Field(
        ...,
        description="Think step by step (reasoning about bet sizing math, GTO play, etc.), and decide what action to take maximizes your expected value.",
    )
    action: Literal["call", "fold", "raise"]
    amount: Optional[int] = Field(None, description="The amount to raise if the action is raise. Otherwise, None.")
