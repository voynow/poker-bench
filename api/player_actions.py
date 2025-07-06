from __future__ import annotations

import random

from constants_and_types import Action, ActionResponse, Player, hand_to_string


def get_random_action(
    player: Player,
    current_bet: int,
    player_chips: int,
) -> ActionResponse:
    if current_bet == 0:
        # No bet to call - can check or bet
        if random.random() < 0.7:
            print(f"   {player.name} decides to CHECK (no bet)")
            return ActionResponse(action=Action.CHECK, amount=0)
        else:
            bet_amount = min(10, player_chips)
            print(f"   {player.name} decides to BET {bet_amount} chips")
            return ActionResponse(action=Action.BET, amount=bet_amount)
    else:
        # There's a bet to call
        if random.random() < 0.6:
            print(f"   {player.name} decides to CALL {current_bet} chips")
            return ActionResponse(action=Action.CALL, amount=current_bet)
        else:
            print(f"   {player.name} decides to FOLD")
            return ActionResponse(action=Action.FOLD, amount=0)


def get_human_action(player: Player, current_bet: int, player_chips: int, pot: int) -> ActionResponse:
    """Get human player action through console input."""

    print("\nYour Turn:")
    print(f"   Current pot: {pot} chips")
    print(f"   Your chips: {player_chips}")
    print(f"   Your cards: {hand_to_string(player.hand)}")

    if current_bet > 0:
        print(f"   You must call {current_bet} chips to stay in the hand")
    else:
        print("   No bet to call - you can check for free")

    while True:
        if current_bet == 0:
            print("\nAvailable actions:")
            print("   [c] CHECK  - Stay in the hand without betting")
            print("   [b] BET    - Make the first bet this round")
            print("   [f] FOLD   - Give up your hand and exit")

            action = input("\nWhat would you like to do? [c/b/f]: ").lower().strip()

            if action in ["c", "check"]:
                return ActionResponse(action=Action.CHECK, amount=0)
            elif action in ["b", "bet"]:
                try:
                    amount = int(input(f"   Enter bet amount (1-{player_chips}): "))
                    if 0 < amount <= player_chips:
                        print(f"You bet {amount} chips")
                        return ActionResponse(action=Action.BET, amount=amount)
                    else:
                        print(f"Invalid amount. Must be between 1 and {player_chips}")
                except ValueError:
                    print("Please enter a valid number")
            elif action in ["f", "fold"]:
                print("You chose to FOLD (give up your hand)")
                return ActionResponse(action=Action.FOLD, amount=0)
            else:
                print("Invalid choice. Please enter 'c', 'b', or 'f'")
        else:
            to_call = current_bet
            print("\nAvailable actions:")
            print(f"   [c] CALL   - Match the current bet of {to_call} chips")
            print(f"   [r] RAISE  - Increase the bet above {current_bet} chips")
            print("   [f] FOLD   - Give up your hand and exit")

            action = input("\nWhat would you like to do? [c/r/f]: ").lower().strip()

            if action in ["c", "call"]:
                print(f"You chose to CALL {to_call} chips")
                return ActionResponse(action=Action.CALL, amount=to_call)
            elif action in ["r", "raise"]:
                print(f"You chose to RAISE. Current bet is {current_bet}")
                try:
                    amount = int(input(f"   Enter your total bet (minimum {current_bet + 1}): "))
                    if amount > current_bet and amount <= player_chips:
                        print(f"You raise to {amount} chips (raising by {amount - current_bet})")
                        return ActionResponse(action=Action.BET, amount=amount)  # Using BET for raise
                    else:
                        print(f"Invalid raise. Must be between {current_bet + 1} and {player_chips}")
                except ValueError:
                    print("Please enter a valid number")
            elif action in ["f", "fold"]:
                print("You chose to FOLD (give up your hand)")
                return ActionResponse(action=Action.FOLD, amount=0)
            else:
                print("Invalid choice. Please enter 'c', 'r', or 'f'")
