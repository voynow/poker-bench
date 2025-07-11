import statistics
from collections import defaultdict
from typing import List

from constants_and_types import GameResult


def print_table(title: str, data: List[tuple[str, str]]) -> None:
    """
    Print a formatted table with consistent styling.

    :param title: The title of the table
    :param data: List of (name, value) tuples to display
    """
    if not data:
        return

    max_name_length = max(len(name) for name, _ in data)
    max_value_length = max(len(value) for _, value in data)

    print()
    print("-" * (max_name_length + max_value_length + 2))
    print(title.center(max_name_length + max_value_length + 2))
    print("-" * (max_name_length + max_value_length + 2))
    for name, value in data:
        print(f"{name:<{max_name_length}}  {value:>{max_value_length}}")
    print("-" * (max_name_length + max_value_length + 2))


def calc_net_chips(game_results: List[GameResult]) -> None:
    """
    Calculate the net chips for each player across all games. The player with the most net chips
    is essentially the strongest player

    :param game_results: A list of GameResult objects
    """
    # Get total net chips for each player across all games
    total_chips = {}
    for game_result in game_results:
        for player in game_result.final_rankings:
            total_chips[player.name] = total_chips.get(player.name, 0) + player.chips
    sorted_total_chips = sorted(total_chips.items(), key=lambda x: x[1], reverse=True)

    data = [(player, f"{chips:,} chips") for player, chips in sorted_total_chips]
    print_table("Total Net Chips", data)
    print("The total net chips across all games")


def calc_chip_volatility(game_results: List[GameResult]) -> None:
    """
    Calculate the volatility of the chip count for each player across all games.
    Lower volatility means more consistent performance.

    :param game_results: A list of GameResult objects
    """
    # Get all unique player names across all games
    all_player_names = set()
    for game_result in game_results:
        for player in game_result.final_rankings:
            all_player_names.add(player.name)
        for player in game_result.eliminated_players:
            all_player_names.add(player.name)

    # Collect chip counts for each player across all games
    player_chips = defaultdict(list)

    for game_result in game_results:
        # Create a dict of player name -> chips for this game
        game_chips = {}

        # Add final rankings (players who made it to the end)
        for player in game_result.final_rankings:
            game_chips[player.name] = player.chips

        # Add eliminated players (with 0 chips)
        for player in game_result.eliminated_players:
            game_chips[player.name] = 0

        # Record chip count for each player in this game
        for player_name in all_player_names:
            if player_name in game_chips:
                player_chips[player_name].append(game_chips[player_name])

    # Calculate volatility (standard deviation) and sort
    volatility_data = []
    for player_name, chips in player_chips.items():
        if len(chips) > 1:
            volatility = statistics.stdev(chips)
        else:
            volatility = 0
        volatility_data.append((player_name, volatility, len(chips)))

    volatility_data.sort(key=lambda x: x[1])  # Sort by volatility (lower is better)

    data = [(name, f"{vol:.0f} chips") for name, vol, games in volatility_data]
    print_table("Chip Volatility", data)
    print("The std dev of chip count across games")


def calc_average_bet_size(game_results: List[GameResult]) -> None:
    """
    Calculate the average bet size for each player across all games.
    Folds and checks count as 0, calls and raises count as their actual amounts.

    :param game_results: A list of GameResult objects
    """
    # Collect bet amounts for each player
    player_bets = defaultdict(list)

    for game_result in game_results:
        for betting_round in game_result.betting_rounds:
            for player, action_response in betting_round.players_actions.items():
                # Record the amount committed (0 for fold/check, actual amount for call/raise)
                player_bets[player.name].append(action_response.amount)

    # Calculate average bet sizes
    avg_bet_data = []
    for player_name, bets in player_bets.items():
        if bets:
            avg_bet = statistics.mean(bets)
            avg_bet_data.append((player_name, avg_bet, len(bets)))

    # Sort by average bet size (descending - higher is more aggressive)
    avg_bet_data.sort(key=lambda x: x[1], reverse=True)

    data = [(name, f"{avg:.1f} chips") for name, avg, actions in avg_bet_data]
    print_table("Average Bet Size", data)
    print("The avg chips committed for each action")


def calc_raise_frequency(game_results: List[GameResult]) -> None:
    """
    Calculate the raise frequency for each player across all games.
    This is the smoking gun metric that shows aggressive vs passive play styles.

    :param game_results: A list of GameResult objects
    """
    # Collect all actions for each player
    player_actions = defaultdict(list)

    for game_result in game_results:
        for betting_round in game_result.betting_rounds:
            for player, action_response in betting_round.players_actions.items():
                player_actions[player.name].append(action_response.action)

    # Calculate raise frequency
    raise_freq_data = []
    for player_name, actions in player_actions.items():
        if actions:
            raise_count = sum(1 for action in actions if action == "raise")
            raise_frequency = (raise_count / len(actions)) * 100
            raise_freq_data.append((player_name, raise_frequency, len(actions)))

    # Sort by raise frequency (descending - higher is more aggressive)
    raise_freq_data.sort(key=lambda x: x[1], reverse=True)

    data = [(name, f"{freq:.1f}%") for name, freq, total_actions in raise_freq_data]
    print_table("Aggressiveness", data)
    print("The % of actions that are raises")


def calc_fold_frequency(game_results: List[GameResult]) -> None:
    """
    Calculate the fold frequency for each player across all games.
    Shows how often players give up - the flip side of aggression.

    :param game_results: A list of GameResult objects
    """
    # Collect all actions for each player
    player_actions = defaultdict(list)

    for game_result in game_results:
        for betting_round in game_result.betting_rounds:
            for player, action_response in betting_round.players_actions.items():
                player_actions[player.name].append(action_response.action)

    # Calculate fold frequency
    fold_freq_data = []
    for player_name, actions in player_actions.items():
        if actions:
            fold_count = sum(1 for action in actions if action == "fold")
            fold_frequency = (fold_count / len(actions)) * 100
            fold_freq_data.append((player_name, fold_frequency, len(actions)))

    # Sort by fold frequency (ascending - lower is more persistent)
    fold_freq_data.sort(key=lambda x: x[1])

    data = [(name, f"{freq:.1f}%") for name, freq, total_actions in fold_freq_data]
    print_table("Passivity", data)
    print("The % of actions that are folds")


def print_metrics(game_results: List[GameResult]):
    """
    Print the metrics for the game results

    :param game_results: A list of GameResult objects
    """
    calc_net_chips(game_results)
    calc_chip_volatility(game_results)
    calc_average_bet_size(game_results)
    calc_raise_frequency(game_results)
    calc_fold_frequency(game_results)
