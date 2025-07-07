from __future__ import annotations

import random

from constants_and_types import Action, ActionResponse, Player
from game import evaluate_hand


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
    # Evaluate current hand strength (just hole cards initially)
    hand_type, tiebreakers = evaluate_hand(player.hand)

    # Get the ranks of our two hole cards
    ranks = sorted([card[0] for card in player.hand], reverse=True)
    high_card, low_card = ranks[0], ranks[1]

    # Determine hand strength category
    is_pair = hand_type == 1
    is_high_pair = is_pair and high_card >= 10  # Tens or better
    is_pocket_pair = is_pair
    has_ace = high_card == 14
    has_face_card = high_card >= 11  # J, Q, K, A
    is_suited = player.hand[0][1] == player.hand[1][1]
    is_connected = abs(high_card - low_card) <= 1

    # Calculate relative bet size
    bet_ratio = amount_to_call / max(player_chips, 1)

    # Strong hands - play aggressively
    if is_high_pair or (is_pocket_pair and high_card >= 7):
        if amount_to_call == 0:
            # No bet to call, bet aggressively
            bet_amount = min(15, player_chips)
            return ActionResponse(action=Action.RAISE, amount=bet_amount)
        elif bet_ratio < 0.3:
            # Small bet relative to our stack, raise
            raise_amount = min(amount_to_call + 15, player_chips)
            return ActionResponse(action=Action.RAISE, amount=raise_amount)
        else:
            # Large bet, but we have a strong hand, call
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)

    # Medium-strong hands - play moderately aggressive
    elif (has_ace and has_face_card) or (is_suited and has_face_card) or (is_connected and has_face_card):
        if amount_to_call == 0:
            # No bet to call, check or small bet
            if random.random() < 0.6:
                return ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = min(10, player_chips)
                return ActionResponse(action=Action.RAISE, amount=bet_amount)
        elif bet_ratio < 0.2:
            # Small bet, call or raise
            if random.random() < 0.7:
                call_amount = min(amount_to_call, player_chips)
                return ActionResponse(action=Action.CALL, amount=call_amount)
            else:
                raise_amount = min(amount_to_call + 10, player_chips)
                return ActionResponse(action=Action.RAISE, amount=raise_amount)
        elif bet_ratio < 0.4:
            # Medium bet, usually call
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)
        else:
            # Large bet, fold more often
            return ActionResponse(action=Action.FOLD, amount=0)

    # Speculative hands - play cautiously
    elif is_suited or is_connected or (low_card >= 7 and high_card >= 10):
        if amount_to_call == 0:
            return ActionResponse(action=Action.CHECK, amount=0)
        elif bet_ratio < 0.15:
            # Very small bet, call
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)
        else:
            # Too expensive, fold
            return ActionResponse(action=Action.FOLD, amount=0)

    # Weak hands - fold most of the time
    else:
        if amount_to_call == 0:
            return ActionResponse(action=Action.CHECK, amount=0)
        elif bet_ratio < 0.1 and random.random() < 0.3:
            # Very small bet, sometimes call as a bluff
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)
        else:
            return ActionResponse(action=Action.FOLD, amount=0)
