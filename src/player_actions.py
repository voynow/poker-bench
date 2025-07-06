from __future__ import annotations

import random
import time

from constants_and_types import Action, ActionResponse, Player, hand_to_string


def get_random_action(
    player: Player,
    current_bet: int,
    player_chips: int,
) -> ActionResponse:
    """
    Get a random action for an AI player

    If no bet to call, check 50% of the time vs bet 50% of the time
    If bet to call, call 50% of the time vs bet 50% of the time

    :param player: The player to get an action for
    :param current_bet: The current bet amount
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """
    _ = player
    _ = player_chips

    if current_bet == 0:
        if random.random() < 0.5:
            return ActionResponse(action=Action.CHECK, amount=0)
        else:
            return ActionResponse(action=Action.BET, amount=10)
    else:
        if random.random() < 0.6:
            return ActionResponse(action=Action.CALL, amount=current_bet)
        elif random.random() < 0.6:
            return ActionResponse(action=Action.FOLD, amount=0)
        else:
            total_bet_amount = current_bet + 10
            return ActionResponse(action=Action.BET, amount=total_bet_amount)


def get_hand_strength_based_action(
    player: Player,
    current_bet: int,
    player_chips: int,
) -> ActionResponse:
    """
    Get a strategic action for an AI player based on hand strength.

    Uses basic hand evaluation to make better decisions than pure randomness.
    Strong hands bet/call more aggressively, weak hands fold more often.

    :param player: The player to get an action for
    :param current_bet: The current bet amount
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """
    from game import evaluate_hand  # Import here to avoid circular imports

    # Evaluate hand strength (0-8, where 8 is best)
    hand_strength, _ = evaluate_hand(player.hand)

    # Calculate hand strength as a percentage (0-1)
    strength_pct = hand_strength / 8.0

    # Check for high cards (J, Q, K, A are 11-14)
    high_cards = [card[0] for card in player.hand if card[0] >= 11]
    has_pair = len(set(card[0] for card in player.hand)) == 1
    has_high_card = len(high_cards) > 0

    # Adjust strength for pre-flop play (only 2 cards)
    if len(player.hand) == 2:
        if has_pair:
            strength_pct = max(0.7, strength_pct)  # Pairs are strong pre-flop
        elif len(high_cards) >= 2:
            strength_pct = max(0.6, strength_pct)  # Two high cards strong
        elif has_high_card:
            strength_pct = max(0.4, strength_pct)  # One high card decent

    # Calculate bet sizing based on hand strength and stack
    max_bet = min(player_chips // 4, 50)  # Don't bet more than 1/4 stack or 50 chips
    min_bet = min(10, player_chips // 10)  # Minimum bet is 10 or 10% of stack

    if current_bet == 0:
        # No bet to call - decide between check and bet
        if strength_pct < 0.3:
            # Weak hand - check most of the time
            if random.random() < 0.85:
                response = ActionResponse(action=Action.CHECK, amount=0)
            else:
                # Small bluff bet occasionally
                bet_amount = min_bet
                response = ActionResponse(action=Action.BET, amount=bet_amount)
        elif strength_pct < 0.6:
            # Medium hand - balanced play
            if random.random() < 0.6:
                response = ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = min_bet + int((max_bet - min_bet) * strength_pct)
                response = ActionResponse(action=Action.BET, amount=bet_amount)
        else:
            # Strong hand - bet for value
            if random.random() < 0.25:
                response = ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = min_bet + int((max_bet - min_bet) * strength_pct)
                response = ActionResponse(action=Action.BET, amount=bet_amount)
    else:
        # There's a bet to call
        call_ratio = min(current_bet / max(player_chips, 1), 1.0)  # How much of stack to call

        if strength_pct < 0.2:
            # Very weak hand - fold almost always
            if random.random() < 0.95:
                response = ActionResponse(action=Action.FOLD, amount=0)
            else:
                response = ActionResponse(action=Action.CALL, amount=current_bet)
        elif strength_pct < 0.4:
            # Weak hand - fold more often, especially to big bets
            fold_chance = 0.7 + (call_ratio * 0.2)  # Higher fold chance for bigger bets
            if random.random() < fold_chance:
                response = ActionResponse(action=Action.FOLD, amount=0)
            else:
                response = ActionResponse(action=Action.CALL, amount=current_bet)
        elif strength_pct < 0.7:
            # Medium hand - call most of the time
            fold_chance = 0.3 + (call_ratio * 0.3)  # Some folding to big bets
            if random.random() < fold_chance:
                response = ActionResponse(action=Action.FOLD, amount=0)
            else:
                response = ActionResponse(action=Action.CALL, amount=current_bet)
        else:
            # Strong hand - call almost always, sometimes raise
            if random.random() < 0.05:
                response = ActionResponse(action=Action.FOLD, amount=0)
            elif random.random() < 0.8:
                response = ActionResponse(action=Action.CALL, amount=current_bet)
            else:
                # Raise with strong hands
                raise_amount = current_bet + min_bet + int((max_bet - min_bet) * strength_pct)
                raise_amount = min(raise_amount, player_chips)
                response = ActionResponse(action=Action.BET, amount=raise_amount)

    return response


def get_human_action(player: Player, current_bet: int, player_chips: int) -> ActionResponse:
    """
    Get human player action through console input

    :param player: The player to get an action for
    :param current_bet: The current bet amount
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """

    print("\nYour Turn:")
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


def get_action_router(player: Player, current_bet: int, player_chips: int) -> ActionResponse:
    """
    Get the appropriate action function for a player

    :param player: The player to get an action for
    :param current_bet: The current bet amount
    :param player_chips: The number of chips the player has
    :return: An ActionResponse object with the action and amount
    """

    if player.name == "You":
        response = get_human_action(player, current_bet, player_chips)
    else:
        response = player.action_func(player, current_bet, player_chips)

    display_str = f"{player.name} {response.action.value}s"
    if response.amount > 0:
        display_str += f" {response.amount} chips"
    print(display_str)
    time.sleep(0.5)
    return response
