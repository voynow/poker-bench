import asyncio
from functools import partial
from typing import List

from tqdm import tqdm

from constants_and_types import STARTING_CHIPS, GameResult, Player
from game import eliminate_players, play_round
from llm import clear_llm_log
from metrics import print_metrics
from player_actions import (
    get_hand_strength_based_action,
    get_llm_one_shot_action,
)


def setup_players() -> List[Player]:
    """
    Setup players of varying player archetypes

    :return: A list of players
    """
    llm_one_shot_4o_mini_action = partial(get_llm_one_shot_action, model="gpt-4o-mini")
    llm_one_shot_4_1_mini_action = partial(get_llm_one_shot_action, model="gpt-4.1-mini")
    llm_one_shot_4_1_nano_action = partial(get_llm_one_shot_action, model="gpt-4.1-nano")
    return [
        Player(name="hand_strength_algo_1", chips=STARTING_CHIPS, hand=[], action_func=get_hand_strength_based_action),
        Player(name="hand_strength_algo_2", chips=STARTING_CHIPS, hand=[], action_func=get_hand_strength_based_action),
        Player(name="hand_strength_algo_3", chips=STARTING_CHIPS, hand=[], action_func=get_hand_strength_based_action),
        Player(name="llm_one_shot_4o_mini", chips=STARTING_CHIPS, hand=[], action_func=llm_one_shot_4o_mini_action),
        Player(name="llm_one_shot_4_1_mini", chips=STARTING_CHIPS, hand=[], action_func=llm_one_shot_4_1_mini_action),
        Player(name="llm_one_shot_4_1_nano", chips=STARTING_CHIPS, hand=[], action_func=llm_one_shot_4_1_nano_action),
    ]


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
    n_games = 10
    max_rounds = 100

    clear_llm_log()
    game_results: List[GameResult] = await run_games(n_games, max_rounds)
    print_metrics(game_results)


if __name__ == "__main__":
    asyncio.run(main())
