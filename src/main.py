import asyncio
import time
from typing import Counter, List

from tqdm import tqdm

from constants_and_types import NUM_OPPONENTS, GameResult, Player
from game import eliminate_players, play_round
from player_actions import (
    get_check_call_action,
    get_hand_strength_based_action,
    get_llm_one_shot_action,
    get_random_action,
)


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
