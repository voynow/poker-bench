import asyncio
from functools import partial
from typing import List

from tqdm import tqdm

from constants_and_types import STARTING_CHIPS, GameResult, Player
from game import eliminate_players, play_round
from llm import clear_llm_log
from metrics import print_metrics
from player_actions import get_llm_one_shot_action, get_llm_reasoning_action


def setup_players() -> List[Player]:
    """
    Setup players of varying player archetypes

    :return: A list of players
    """
    models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano"]
    strategies = [
        ("one_shot", get_llm_one_shot_action),
        ("reasoning", get_llm_reasoning_action),
    ]

    players = []
    for model in models:
        for strategy_name, strategy_func in strategies:
            name = f"{strategy_name}_{model}"
            action_func = partial(strategy_func, model=model, function_name=name)

            players.append(Player(name=name, chips=STARTING_CHIPS, hand=[], action_func=action_func))

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
    all_betting_rounds = []
    while round_count < max_rounds and len(players) >= 2:
        round_betting_results = await play_round(round_number=round_count, players=players)
        all_betting_rounds.extend(round_betting_results)
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
        betting_rounds=all_betting_rounds,
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
    n_games = 100
    max_rounds = 100

    clear_llm_log()
    game_results: List[GameResult] = await run_games(n_games, max_rounds)
    print_metrics(game_results)


if __name__ == "__main__":
    asyncio.run(main())
