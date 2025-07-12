from __future__ import annotations

import random
from itertools import combinations
from typing import Dict, List, Tuple

from constants_and_types import (
    RANKS,
    Action,
    BettingRound,
    BettingRoundResult,
    Card,
    Hand,
    Player,
    Suit,
)


def create_deck() -> List[Card]:
    """Create a standard 52-card deck in order of suits and ranks."""
    return [(rank_val, suit) for rank_val in range(2, 15) for suit in Suit]


def deal_cards(deck: List[Card], num_cards: int) -> List[Card]:
    """Deal num_cards from the deck."""
    return [deck.pop() for _ in range(num_cards)]


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


def setup_round(players: List[Player]) -> List[Card]:
    """Setup initial game state with players (modified in place) and shuffled deck."""
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


def get_winners_from_hands(player_hands: Dict[Player, Tuple[int, List[int]]]) -> List[Player]:
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
        remainder = pot % len(winners)

        # Give each winner their share
        for winner in winners:
            winner.chips += split_amount

        # Give remainder to first winner(s) to avoid losing chips
        for i in range(remainder):
            winners[i].chips += 1

        return split_amount


def calculate_max_callable_amount(
    raising_player: Player, player_bets: Dict[Player, int], active_players: List[Player]
) -> int:
    """Calculate the maximum amount that can be called by all players.

    This is based on the smallest stack - the pot should never include more
    than what the shortest-stacked opponent can call.
    """
    if len(active_players) <= 1:
        return player_bets[raising_player] + raising_player.chips

    min_callable = float("inf")

    for player in active_players:
        if player == raising_player:
            continue

        # How much this player can contribute total (current bet + remaining chips)
        max_contribution = player_bets[player] + player.chips
        min_callable = min(min_callable, max_contribution)

    return min_callable


def process_betting_action(
    player: Player,
    action: Action,
    amount: int,
    player_bets: Dict[Player, int],
    pot: int,
    current_bet: int,
    active_players: List[Player],
) -> Tuple[int, int, bool, int]:
    """Process a betting action and return updated pot, current_bet, whether there was a raise, and actual amount contributed."""

    if action == Action.FOLD:
        active_players.remove(player)
        return pot, current_bet, False, 0
    elif action == Action.CHECK:
        return pot, current_bet, False, 0
    elif action == Action.CALL:
        # Calculate how much the player actually needs to call
        to_call = current_bet - player_bets[player]
        actual_call_amount = min(to_call, player.chips)

        player_bets[player] += actual_call_amount
        player.chips -= actual_call_amount
        pot += actual_call_amount

        return pot, current_bet, False, actual_call_amount
    elif action == Action.RAISE:
        # Calculate maximum callable amount by other players
        max_callable = calculate_max_callable_amount(player, player_bets, active_players)

        # Determine the effective raise amount (capped by what others can call AND player's chips)
        proposed_total_bet = player_bets[player] + amount
        max_player_can_bet = player_bets[player] + player.chips
        effective_total_bet = min(proposed_total_bet, max_callable, max_player_can_bet)

        # Calculate actual amount to take from player's chips
        actual_amount = effective_total_bet - player_bets[player]

        # Update player's state (only subtract what we're actually using)
        player_bets[player] = effective_total_bet
        player.chips -= actual_amount
        pot += actual_amount

        new_current_bet = effective_total_bet
        was_raise = new_current_bet > current_bet

        return pot, new_current_bet, was_raise, actual_amount
    else:
        raise ValueError(f"Invalid action: {action}")


def all_players_all_in(active_players: List[Player]) -> bool:
    """Check if all active players are all-in (have 0 chips)."""
    return all(player.chips == 0 for player in active_players)


async def betting_round(
    round_number: int,
    active_players: List[Player],
    pot: int,
    community_cards: List[Card],
    betting_round_type: BettingRound,
    current_bet: int = 0,
    blinds: Dict[Player, int] = None,
) -> BettingRoundResult:
    """Handle a betting round with AI players only."""
    starting_pot = pot

    # Skip betting if all players are all-in
    if all_players_all_in(active_players):
        return BettingRoundResult(
            round_number=round_number,
            betting_round_type=betting_round_type,
            players_actions={},
            starting_pot=starting_pot,
            final_pot=pot,
            community_cards=community_cards,
            active_players=active_players,
        )

    players_to_act = list(active_players)
    player_bets = blinds.copy() if blinds else {player: 0 for player in active_players}
    players_actions = {}

    while len(players_to_act) > 0:
        player = players_to_act.pop(0)

        if player not in active_players:
            continue

        to_call = current_bet - player_bets[player]

        action_func = player.action_func
        action_response = await action_func(player, pot, to_call, player.chips, community_cards, betting_round_type)

        # Process the action using game logic
        pot, current_bet, was_raise, actual_amount = process_betting_action(
            player, action_response.action, action_response.amount, player_bets, pot, current_bet, active_players
        )

        # Update the action response with the actual amount contributed
        action_response.actual_amount_contributed = actual_amount

        # Store the action response for this player
        players_actions[player] = action_response

        # If there was a raise, add other players back to act
        if was_raise:
            for other_player in active_players:
                if other_player != player and other_player not in players_to_act:
                    # Add players who haven't matched the new current bet
                    if player_bets[other_player] < current_bet:
                        players_to_act.append(other_player)

        # Check if only one player remains
        if len(active_players) == 1:
            break

        # Check if all remaining players are all-in
        if all_players_all_in(active_players):
            break

    return BettingRoundResult(
        round_number=round_number,
        betting_round_type=betting_round_type,
        players_actions=players_actions,
        starting_pot=starting_pot,
        final_pot=pot,
        community_cards=community_cards,
        active_players=active_players,
    )


async def play_round(round_number: int, players: List[Player]) -> List[BettingRoundResult]:
    """Play a single round of Texas Hold'em."""
    deck = setup_round(players)
    betting_round_results = []

    # Apply blinds
    pot, small_blind_player, big_blind_player = apply_blinds(players)
    small_blind, big_blind = 5, 10
    current_bet = big_blind

    # Pre-flop: rotate so action starts with player to left of big blind
    active_players = players[2:] + players[:2]  # Move first 2 players to end

    # Pre-flop betting round
    if len(active_players) > 1:
        blind_bets = {player: 0 for player in active_players}
        blind_bets[small_blind_player] = small_blind
        blind_bets[big_blind_player] = big_blind

        betting_round_result = await betting_round(
            round_number=round_number,
            active_players=active_players,
            pot=pot,
            community_cards=[],
            betting_round_type=BettingRound.PRE_FLOP,
            current_bet=current_bet,
            blinds=blind_bets,
        )
        betting_round_results.append(betting_round_result)

    # Post-flop: put small blind first (if still active)
    active_players = betting_round_result.active_players
    if len(active_players) > 1 and small_blind_player in active_players:
        sb_idx = active_players.index(small_blind_player)
        active_players = active_players[sb_idx:] + active_players[:sb_idx]

    # Deal flop (3 community cards)
    community_cards = []
    if len(active_players) > 1:
        deck.pop()  # Burn card
        for _ in range(3):
            community_cards.append(deck.pop())
        if not all_players_all_in(active_players):
            betting_round_result = await betting_round(
                round_number=round_number,
                active_players=active_players,
                pot=betting_round_result.final_pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.FLOP,
            )
            betting_round_results.append(betting_round_result)

    # Deal turn (1 community card)
    if len(betting_round_result.active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(betting_round_result.active_players):
            betting_round_result = await betting_round(
                round_number=round_number,
                active_players=betting_round_result.active_players,
                pot=betting_round_result.final_pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.TURN,
            )
            betting_round_results.append(betting_round_result)

    # Deal river (1 community card)
    if len(betting_round_result.active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(betting_round_result.active_players):
            betting_round_result = await betting_round(
                round_number=round_number,
                active_players=betting_round_result.active_players,
                pot=betting_round_result.final_pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.RIVER,
            )
            betting_round_results.append(betting_round_result)

    # Distribute pot to winner(s)
    final_active_players = betting_round_result.active_players
    final_pot = betting_round_result.final_pot

    if len(final_active_players) == 1:
        winner = final_active_players[0]
        winner.chips += final_pot
    elif len(final_active_players) > 1:
        # Showdown - determine winners and distribute pot
        player_hands = determine_winners(final_active_players, community_cards)
        winners = get_winners_from_hands(player_hands)
        distribute_winnings(winners, final_pot)

    return betting_round_results


def eliminate_players(players: List[Player]) -> Tuple[List[Player], List[Player]]:
    """
    Remove players with 0 chips from the game.

    :param players: A list of players
    :return: A tuple containing the remaining players and the eliminated players
    """
    remaining_players = [p for p in players if p.chips > 0]
    eliminated_players = [p for p in players if p.chips <= 0]
    return remaining_players, eliminated_players
