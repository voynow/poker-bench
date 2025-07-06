from __future__ import annotations

import random
import time

from constants_and_types import Action, ActionResponse, Player, hand_to_string


def get_random_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
) -> ActionResponse:
    """
    Get a random action for an AI player

    If no bet to call, check 50% of the time vs bet 50% of the time
    If bet to call, call 50% of the time vs bet 50% of the time

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """
    if amount_to_call == 0:
        if random.random() < 0.75:
            return ActionResponse(action=Action.CHECK, amount=0)
        else:
            return ActionResponse(action=Action.RAISE, amount=amount_to_call + 10)
    else:
        if random.random() < 0.75:
            return ActionResponse(action=Action.CALL, amount=amount_to_call)
        elif random.random() < 0.75:
            return ActionResponse(action=Action.FOLD, amount=0)
        else:
            total_bet_amount = amount_to_call + 10
            return ActionResponse(action=Action.RAISE, amount=total_bet_amount)


def get_hand_strength_based_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
) -> ActionResponse:
    """
    Get a strategic action for an AI player based on hand strength.

    Uses basic hand evaluation to make better decisions than pure randomness.
    Strong hands bet/call more aggressively, weak hands fold more often.

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """
    from game import evaluate_hand

    # Evaluate hand strength (0-8, where 8 is best)
    hand_strength, _ = evaluate_hand(player.hand)

    # Calculate hand strength percentage (0.0 to 1.0)
    strength_ratio = hand_strength / 8.0

    # Very weak hands (0-2): mostly fold, sometimes check/call
    if hand_strength <= 2:
        if amount_to_call == 0:
            return ActionResponse(action=Action.CHECK, amount=0)
        elif amount_to_call <= 5:  # Small bet
            if random.random() < 0.3:
                return ActionResponse(action=Action.CALL, amount=amount_to_call)
            else:
                return ActionResponse(action=Action.FOLD, amount=0)
        else:
            return ActionResponse(action=Action.FOLD, amount=0)

    # Moderate hands (3-5): balanced play
    elif hand_strength <= 5:
        if amount_to_call == 0:
            if random.random() < 0.7:
                return ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = int(5 + (strength_ratio * 10))
                return ActionResponse(action=Action.RAISE, amount=bet_amount)
        else:
            if amount_to_call <= 15:
                if random.random() < 0.7:
                    return ActionResponse(action=Action.CALL, amount=amount_to_call)
                else:
                    return ActionResponse(action=Action.FOLD, amount=0)
            else:
                if random.random() < 0.3:
                    return ActionResponse(action=Action.CALL, amount=amount_to_call)
                else:
                    return ActionResponse(action=Action.FOLD, amount=0)

    # Strong hands (6-8): aggressive play
    else:
        if amount_to_call == 0:
            if random.random() < 0.3:
                return ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = int(10 + (strength_ratio * 20))
                return ActionResponse(action=Action.RAISE, amount=bet_amount)
        else:
            if random.random() < 0.8:
                return ActionResponse(action=Action.CALL, amount=amount_to_call)
            else:
                raise_amount = amount_to_call + int(10 + (strength_ratio * 15))
                return ActionResponse(action=Action.RAISE, amount=raise_amount)


def get_human_action(player: Player, amount_to_call: int, player_chips: int) -> ActionResponse:
    """
    Get human player action through console input

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """

    print("\nYour Turn:")
    print(f"   Your chips: {player_chips}")
    print(f"   Your cards: {hand_to_string(player.hand)}")

    if amount_to_call > 0:
        print(f"   You must call {amount_to_call} chips to stay in the hand")
    else:
        print("   No bet to call - you can check for free")

    while True:
        if amount_to_call > 0:
            print("\nAvailable actions:")
            print("   Call (c)")
            print("   Fold (f)")
            print("   Raise (r)")
            choice = input("Choose your action (c/f/r): ").strip()

            if choice == "c":
                if amount_to_call > player_chips:
                    print(f"You don't have enough chips to call! You have {player_chips}, need {amount_to_call}")
                    continue
                return ActionResponse(action=Action.CALL, amount=amount_to_call)
            elif choice == "f":
                return ActionResponse(action=Action.FOLD, amount=0)
            elif choice == "r":
                min_raise = amount_to_call + 1
                if min_raise > player_chips:
                    print(f"You don't have enough chips to raise! You have {player_chips}, need at least {min_raise}")
                    continue

                while True:
                    try:
                        raise_amount = int(input(f"Enter raise amount (minimum {min_raise}): ").strip())
                        if raise_amount < min_raise:
                            print(f"Raise amount must be at least {min_raise}")
                            continue
                        if raise_amount > player_chips:
                            print(f"You don't have enough chips! You have {player_chips}")
                            continue
                        return ActionResponse(action=Action.RAISE, amount=raise_amount)
                    except ValueError:
                        print("Please enter a valid number")
            else:
                print("Invalid choice. Please enter c, f, or r.")
        else:
            print("\nAvailable actions:")
            print("   Check (c)")
            print("   Raise (r)")
            choice = input("Choose your action (c/r): ").strip()

            if choice == "c":
                return ActionResponse(action=Action.CHECK, amount=0)
            elif choice == "r":
                min_raise = 1
                if min_raise > player_chips:
                    print(f"You don't have enough chips to raise! You have {player_chips}")
                    continue

                while True:
                    try:
                        raise_amount = int(input(f"Enter raise amount (minimum {min_raise}): ").strip())
                        if raise_amount < min_raise:
                            print(f"Raise amount must be at least {min_raise}")
                            continue
                        if raise_amount > player_chips:
                            print(f"You don't have enough chips! You have {player_chips}")
                            continue
                        return ActionResponse(action=Action.RAISE, amount=raise_amount)
                    except ValueError:
                        print("Please enter a valid number")
            else:
                print("Invalid choice. Please enter c or r.")


def get_action_router(player: Player, amount_to_call: int, player_chips: int) -> ActionResponse:
    """
    Get the appropriate action function for a player

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """

    if player.name == "You":
        response = get_human_action(player, amount_to_call, player_chips)
    else:
        response = player.action_func(player, amount_to_call, player_chips)

    display_str = f"{player.name} {response.action.value}s"
    if response.amount > 0:
        display_str += f" {response.amount} chips"
    print(display_str)
    time.sleep(0.5)
    return response
