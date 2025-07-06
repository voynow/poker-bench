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
            # If we want to call but don't have enough chips, go all-in
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)
        elif random.random() < 0.75:
            return ActionResponse(action=Action.FOLD, amount=0)
        else:
            # If we want to raise but don't have enough chips, go all-in
            total_bet_amount = min(amount_to_call + 10, player_chips)
            if total_bet_amount > amount_to_call:
                return ActionResponse(action=Action.RAISE, amount=total_bet_amount)
            else:
                # Can't raise, just call or fold
                if total_bet_amount >= amount_to_call:
                    return ActionResponse(action=Action.CALL, amount=amount_to_call)
                else:
                    return ActionResponse(action=Action.FOLD, amount=0)


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
    pass


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
                    print(f"You don't have enough chips to call the full amount!")
                    print(f"You have {player_chips} chips, need {amount_to_call}")
                    print(f"Going all-in with {player_chips} chips")
                    return ActionResponse(action=Action.CALL, amount=player_chips)
                return ActionResponse(action=Action.CALL, amount=amount_to_call)
            elif choice == "f":
                return ActionResponse(action=Action.FOLD, amount=0)
            elif choice == "r":
                min_raise = amount_to_call + 1
                if min_raise > player_chips:
                    print(f"You don't have enough chips to raise! You have {player_chips}, need at least {min_raise}")
                    print("You can only call or fold.")
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
    return response
