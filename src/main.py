import asyncio
import time
from typing import Counter, Dict, List, Optional, Tuple

from tqdm import tqdm

from constants_and_types import NUM_OPPONENTS, BettingRound, BettingRoundResult, Card, GameResult, Player
from game import (
    apply_blinds,
    determine_winners,
    distribute_winnings,
    get_winners_from_hands,
    process_betting_action,
    setup_round,
)
from player_actions import (
    get_check_call_action,
    get_hand_strength_based_action,
    get_llm_one_shot_action,
    get_random_action,
)


def all_players_all_in(active_players: List[Player]) -> bool:
    """Check if all active players are all-in (have 0 chips)."""
    return all(player.chips == 0 for player in active_players)


async def betting_round(
    active_players: List[Player],
    pot: int,
    community_cards: List[Card],
    betting_round_type: BettingRound,
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
        action_response = await action_func(player, to_call, player.chips, community_cards, betting_round_type)

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
            active_players=active_players,
            pot=pot,
            community_cards=[],
            betting_round_type=BettingRound.PRE_FLOP,
            current_bet=current_bet,
            blinds=blind_bets,
        )

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
                active_players=active_players,
                pot=betting_round_result.pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.FLOP,
            )

    # Deal turn (1 community card)
    if len(betting_round_result.active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(betting_round_result.active_players):
            betting_round_result = await betting_round(
                active_players=betting_round_result.active_players,
                pot=betting_round_result.pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.TURN,
            )

    # Deal river (1 community card)
    if len(betting_round_result.active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        if not all_players_all_in(betting_round_result.active_players):
            betting_round_result = await betting_round(
                active_players=betting_round_result.active_players,
                pot=betting_round_result.pot,
                community_cards=community_cards,
                betting_round_type=BettingRound.RIVER,
            )

    # Distribute pot to winner(s)
    final_active_players = betting_round_result.active_players
    final_pot = betting_round_result.pot

    if len(final_active_players) == 1:
        winner = final_active_players[0]
        winner.chips += final_pot
    elif len(final_active_players) > 1:
        # Showdown - determine winners and distribute pot
        player_hands = determine_winners(final_active_players, community_cards)
        winners = get_winners_from_hands(player_hands)
        distribute_winnings(winners, final_pot)


def eliminate_players(players: List[Player]) -> Tuple[List[Player], Optional[List[Player]]]:
    """Remove players with 0 chips from the game."""
    remaining_players = [p for p in players if p.chips > 0]
    eliminated_players = [p for p in players if p.chips <= 0]
    return remaining_players, eliminated_players


def setup_players() -> List[Player]:
    """
    Setup players of varying player archetypes

    :param num_players: The number of players to setup
    :return: A list of players
    """
    players: List[Player] = []

    player_archetypes = [
        get_check_call_action,
        get_hand_strength_based_action,
        get_random_action,
        get_llm_one_shot_action,
    ]
    player_archetypes_counts = {func: 1 for func in player_archetypes}

    while len(players) < NUM_OPPONENTS:
        for func in player_archetypes:
            name = f"{func.__name__},{player_archetypes_counts[func]}"
            players.append(Player(name=name, chips=1000, hand=[], action_func=func))
            player_archetypes_counts[func] += 1

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


async def run_games(n_games: int, max_rounds: int) -> List[GameResult]:
    """
    Run a number of poker games and return the results.

    :param n_games: The number of games to run
    :param max_rounds: The maximum number of rounds to play
    :return: A list of GameResult objects
    """
    semaphore = asyncio.Semaphore(100)
    pbar = tqdm(total=n_games, desc="Running poker simulations", unit="games")

    async def run_game():
        async with semaphore:
            result = await collect_game_result(max_rounds)
            pbar.update(1)
            return result

    # Run all games and collect results
    game_results = await asyncio.gather(*[run_game() for _ in range(n_games)])
    pbar.close()

    return game_results


async def main():
    start_time = time.time()
    n_games = 100
    max_rounds = 100

    game_results = await run_games(n_games, max_rounds)

    # Process results
    results = {
        "winning_strategy": [r.winner for r in game_results],
        "rounds_played": [r.rounds_played for r in game_results],
        "final_rankings": [r.final_rankings for r in game_results],
        "players_eliminated": [r.eliminated_players for r in game_results],
    }

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    print(f"Done in {minutes}m {seconds}s")

    winning_strategies = [res.split(",")[0] for res in results["winning_strategy"]]
    strategy_counts = Counter(winning_strategies)
    total_games = len(winning_strategies)

    print("\nWinning Strategy Results:")
    print("-" * 40)
    for strategy, count in strategy_counts.most_common():
        percentage = (count / total_games) * 100
        print(f"{strategy:<30} {count:>3} ({percentage:>5.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
