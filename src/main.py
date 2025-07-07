import asyncio
import time
from typing import Dict, List, Optional, Tuple

from constants_and_types import NUM_OPPONENTS, BettingRoundResult, GameResult, Player
from game import (
    apply_blinds,
    determine_winners,
    distribute_winnings,
    get_winners_from_hands,
    process_betting_action,
    setup_round,
)
from player_actions import get_hand_strength_based_action, get_placeholder_async_action, get_random_action


def all_players_all_in(active_players: List[Player]) -> bool:
    """Check if all active players are all-in (have 0 chips)."""
    return all(player.chips == 0 for player in active_players)


async def betting_round(
    active_players: List[Player],
    pot: int,
    current_bet: int = 0,
    blinds: Dict[Player, int] = None,
) -> BettingRoundResult:
    """Handle a betting round with AI players only."""

    # Skip betting if all players are all-in
    if all_players_all_in(active_players):
        return BettingRoundResult(pot=pot, active_players=active_players)

    players_to_act = list(active_players)
    player_bets = blinds.copy() if blinds else {player: 0 for player in active_players}

    while len(players_to_act) > 0:
        player = players_to_act.pop(0)

        if player not in active_players:
            continue

        to_call = current_bet - player_bets[player]

        action_func = player.action_func
        action_response = await action_func(player, to_call, player.chips)

        # Process the action using game logic
        pot, current_bet, was_raise = process_betting_action(
            player, action_response.action, action_response.amount, player_bets, pot, current_bet, active_players
        )

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

    return BettingRoundResult(pot=pot, active_players=active_players)


async def play_round(players: List[Player]):
    """Play a single round of Texas Hold'em."""
    deck = setup_round(players)

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
            active_players=active_players, pot=pot, current_bet=current_bet, blinds=blind_bets
        )

    # Post-flop: put small blind first (if still active)
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
                active_players=betting_round_result.active_players, pot=betting_round_result.pot
            )

    # Deal turn (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(active_players):
            betting_round_result = await betting_round(
                active_players=betting_round_result.active_players, pot=betting_round_result.pot
            )

    # Deal river (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(active_players):
            betting_round_result = await betting_round(
                active_players=betting_round_result.active_players, pot=betting_round_result.pot
            )

    # Distribute pot to winner(s)
    if len(active_players) == 1:
        winner = active_players[0]
        winner.chips += pot
    elif len(active_players) > 1:
        # Showdown - determine winners and distribute pot
        player_hands = determine_winners(active_players, community_cards)
        winners = get_winners_from_hands(player_hands)
        distribute_winnings(winners, pot)


def eliminate_players(players: List[Player]) -> Tuple[List[Player], Optional[List[Player]]]:
    """Remove players with 0 chips from the game."""
    remaining_players = [p for p in players if p.chips > 0]
    eliminated_players = [p for p in players if p.chips <= 0]
    return remaining_players, eliminated_players


def setup_players() -> List[Player]:
    """
    Setup players: 1 strategic player, 1 placeholder player, and the rest random players

    :param num_players: The number of players to setup
    :return: A list of players
    """
    players: List[Player] = []

    for i in range(NUM_OPPONENTS - 2):
        action_func = get_random_action
        name = f"Random {i + 1}"
        player = Player(name=name, chips=1000, hand=[], action_func=action_func)
        players.append(player)

    players.append(Player(name="Strategic", chips=1000, hand=[], action_func=get_hand_strength_based_action))
    players.append(Player(name="Placeholder", chips=1000, hand=[], action_func=get_placeholder_async_action))
    return players


async def collect_game_result(max_rounds: int) -> GameResult:
    """
    Play a single game and return its results.

    :param max_rounds: The maximum number of rounds to play
    :return: A GameResult containing the winner, rounds played, final rankings, and eliminated players
    """
    players = setup_players()

    round_count = 0
    eliminated_players = []
    while round_count < max_rounds and len(players) >= 2:
        await play_round(players)
        players, eliminated_this_round = eliminate_players(players)
        eliminated_players.extend(eliminated_this_round)
        round_count += 1

    winner = sorted(players, key=lambda p: p.chips, reverse=True)[0].name
    final_rankings = sorted(players, key=lambda p: p.chips, reverse=True)

    return GameResult(
        winner=winner,
        rounds_played=round_count,
        final_rankings=final_rankings,
        eliminated_players=eliminated_players,
    )


async def main():
    start_time = time.time()
    n_games = 100
    max_rounds = 25

    game_tasks = [collect_game_result(max_rounds) for _ in range(n_games)]
    game_results = await asyncio.gather(*game_tasks)

    results = {
        "winning_strategy": [],
        "rounds_played": [],
        "final_rankings": [],
        "players_eliminated": [],
    }

    for game_result in game_results:
        results["winning_strategy"].append(game_result.winner)
        results["rounds_played"].append(game_result.rounds_played)
        results["final_rankings"].append(game_result.final_rankings)
        results["players_eliminated"].append(game_result.eliminated_players)

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    print(f"Done in {minutes}m {seconds}s")

    strategic_wins = results["winning_strategy"].count("Strategic")
    placeholder_wins = results["winning_strategy"].count("Placeholder")
    random_wins = len(results["winning_strategy"]) - strategic_wins - placeholder_wins
    print(f"Strategic player won {strategic_wins / n_games * 100:.2f}% of games")
    print(f"Placeholder player won {placeholder_wins / n_games * 100:.2f}% of games")
    print(f"Random player won {random_wins / n_games * 100:.2f}% of games")


if __name__ == "__main__":
    asyncio.run(main())
