from __future__ import annotations

import random
from itertools import combinations
from typing import Dict, List, Tuple

from constants_and_types import RANKS, Action, Card, Hand, Player, Suit
from player_actions import get_human_action, get_random_action


def create_deck() -> List[Card]:
    """Create a standard 52-card deck in order of suits and ranks."""
    return [(rank_val, suit) for rank_val in range(2, 15) for suit in Suit]


def deal_cards(deck: List[Card], num_cards: int) -> List[Card]:
    """Deal num_cards from the deck."""
    return [deck.pop() for _ in range(num_cards)]


def print_card_visual(card: Card) -> str:
    """Return a visual representation of a card."""
    rank, suit = card
    rank_str = RANKS[rank - 2]
    return f"{rank_str}{suit.value}"


def evaluate_hand(hand: Hand) -> Tuple[int, List[int]]:
    """
    Evaluate poker hand strength.
    Returns (hand_type, tiebreaker_values) where higher is better.
    """
    ranks = sorted([card[0] for card in hand], reverse=True)
    suits = [card[1] for card in hand]

    # Count ranks
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), reverse=True)

    # Check for flush
    is_flush = len(set(suits)) == 1

    # Check for straight
    is_straight = False
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
        # Special case: A-2-3-4-5 straight (wheel)
        elif unique_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            unique_ranks = [5, 4, 3, 2, 1]  # Ace low

    # Hand rankings (higher number = better hand)
    if is_straight and is_flush:
        return (8, unique_ranks)  # Straight flush
    elif counts == [4, 1]:
        return (
            7,
            [rank for rank, count in rank_counts.items() if count == 4]
            + [rank for rank, count in rank_counts.items() if count == 1],
        )  # Four of a kind
    elif counts == [3, 2]:
        return (
            6,
            [rank for rank, count in rank_counts.items() if count == 3]
            + [rank for rank, count in rank_counts.items() if count == 2],
        )  # Full house
    elif is_flush:
        return (5, unique_ranks)  # Flush
    elif is_straight:
        return (4, unique_ranks)  # Straight
    elif counts == [3, 1, 1]:
        return (
            3,
            [rank for rank, count in rank_counts.items() if count == 3]
            + sorted(
                [rank for rank, count in rank_counts.items() if count == 1],
                reverse=True,
            ),
        )
    elif counts == [2, 2, 1]:
        pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
        kicker = [rank for rank, count in rank_counts.items() if count == 1]
        return (2, pairs + kicker)
    elif counts == [2, 1, 1, 1]:
        pair = [rank for rank, count in rank_counts.items() if count == 2]
        kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
        return (1, pair + kickers)  # One pair
    else:
        return (0, unique_ranks)  # High card


def best_hand_from_seven(cards: List[Card]) -> Tuple[int, List[int]]:
    """Find the best 5-card hand from 7 cards."""
    best_score = (-1, [])

    for combo in combinations(cards, 5):
        hand_type, tiebreakers = evaluate_hand(list(combo))
        score = (hand_type, tiebreakers)
        if score > best_score:
            best_score = score

    return best_score[0], best_score[1]


def setup_players(num_players: int) -> List[Player]:
    """
    Setup players with self + num_players - 1 AI players

    :param num_players: The number of players to setup
    :return: A list of players
    """
    players: List[Player] = []
    players.append(Player(name="You", chips=1000, hand=[], action_func=get_human_action))

    for i in range(num_players - 1):
        ai_player = Player(name=f"Player {i + 1}", chips=1000, hand=[], action_func=get_random_action)
        players.append(ai_player)

    return players


def setup_round(players: List[Player]) -> Tuple[List[Player], List[Card]]:
    """
    Setup initial game state with players (modified in place) and shuffled deck

    :param players: The players to setup
    :return: A shuffled deck
    """
    deck = create_deck()
    random.shuffle(deck)

    # ensure each player has an empty hand
    for player in players:
        player.hand = []

    # Deal hole cards
    for _ in range(2):
        for player in players:
            player.hand.append(deck.pop())

    return deck


def apply_blinds(players: List[Player], small_blind: int = 5, big_blind: int = 10) -> Tuple[int, Player, Player]:
    """Apply blinds and return pot size and blind players."""
    # Randomly rotate players for blind positions
    rotate_index = random.randint(0, len(players) - 1)
    for _ in range(rotate_index):
        players.append(players.pop(0))

    small_blind_player = players[0]
    big_blind_player = players[1]

    small_blind_player.chips -= small_blind
    big_blind_player.chips -= big_blind
    pot = small_blind + big_blind

    return pot, small_blind_player, big_blind_player


def determine_winners(active_players: List[Player], community_cards: List[Card]) -> Dict[Player, Tuple[int, List[int]]]:
    """Determine winners from showdown."""
    player_hands = {}
    for player in active_players:
        all_cards = player.hand + community_cards
        hand_type, tiebreakers = best_hand_from_seven(all_cards)
        player_hands[player] = (hand_type, tiebreakers)

    return player_hands


def get_winners_from_hands(player_hands: Dict[Player, Tuple[int, List[int], List[Card]]]) -> List[Player]:
    """Get list of winning players from hand evaluations."""
    best_score = max(player_hands.values(), key=lambda x: (x[0], x[1]))
    winners = [
        player
        for player, hand_data in player_hands.items()
        if (hand_data[0], hand_data[1]) == (best_score[0], best_score[1])
    ]
    return winners


def distribute_winnings(winners: List[Player], pot: int) -> int:
    """Distribute pot to winners and return amount each winner gets."""
    if len(winners) == 1:
        winners[0].chips += pot
        return pot
    else:
        # Split pot among winners
        split_amount = pot // len(winners)
        for winner in winners:
            winner.chips += split_amount
        return split_amount


def process_betting_action(
    player: Player,
    action: Action,
    amount: int,
    player_bets: Dict[Player, int],
    pot: int,
    current_bet: int,
    active_players: List[Player],
) -> Tuple[int, int, bool]:
    """
    Process a betting action and return updated pot, current_bet, and whether there was a raise.

    Returns: (new_pot, new_current_bet, was_raise)
    """

    if action == Action.FOLD:
        active_players.remove(player)
        return pot, current_bet, False
    elif action == Action.CHECK:
        return pot, current_bet, False
    elif action == Action.CALL:
        player_bets[player] += amount
        player.chips -= amount
        pot += amount
        print(f"   Pot is now {pot} chips")
        return pot, current_bet, False
    elif action == Action.RAISE:
        player_bets[player] += amount
        player.chips -= amount
        pot += amount
        new_current_bet = player_bets[player]

        # Only consider it a raise if the new bet is higher than the current bet
        was_raise = new_current_bet > current_bet

        print(f"   Pot is now {pot} chips")
        return pot, new_current_bet, was_raise
    else:
        raise ValueError(f"Invalid action: {action}")
