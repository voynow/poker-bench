from __future__ import annotations

import random
from textwrap import dedent
from typing import List

from constants_and_types import (
    Action,
    ActionResponse,
    BettingRound,
    CallFoldOrRaise,
    CallFoldOrRaiseWithReasoning,
    Card,
    CheckOrRaise,
    CheckOrRaiseWithReasoning,
    Player,
    hand_to_string,
)
from game import best_hand_from_seven, evaluate_hand
from llm import get_completion_structured


async def get_random_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
    community_cards: List[Card],
    betting_round: BettingRound,
) -> ActionResponse:
    """
    Get a random action for an AI player

    If no bet to call, check 50% of the time vs bet 50% of the time
    If bet to call, call 50% of the time vs bet 50% of the time

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :param community_cards: The community cards currently on the table
    :param betting_round: The current betting round
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


async def get_hand_strength_based_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
    community_cards: List[Card],
    betting_round: BettingRound,
) -> ActionResponse:
    """
    Get a strategic action for an AI player based on hand strength.

    Uses basic hand evaluation to make better decisions than pure randomness.
    Strong hands bet/call more aggressively, weak hands fold more often.

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :param community_cards: The community cards currently on the table
    :param betting_round: The current betting round
    :return: An ActionResponse object with the action and amount
    """
    # Evaluate current hand strength
    if community_cards:
        # Post-flop: use best hand from hole cards + community cards
        all_cards = player.hand + community_cards
        hand_type, tiebreakers = best_hand_from_seven(all_cards)
    else:
        # Pre-flop: just hole cards
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

    # Adjust strategy based on hand strength (post-flop hands are stronger)
    hand_strength_multiplier = 1.0
    if community_cards:
        # Post-flop: stronger hands (pairs, two pair, etc.) get more aggressive
        if hand_type >= 2:  # Two pair or better
            hand_strength_multiplier = 2.0
        elif hand_type == 1:  # One pair
            hand_strength_multiplier = 1.5

    # Strong hands - play aggressively
    if is_high_pair or (is_pocket_pair and high_card >= 7) or (hand_type >= 2 and community_cards):
        if amount_to_call == 0:
            # No bet to call, bet aggressively
            bet_amount = min(int(15 * hand_strength_multiplier), player_chips)
            return ActionResponse(action=Action.RAISE, amount=bet_amount)
        elif bet_ratio < 0.3:
            # Small bet relative to our stack, raise
            raise_amount = min(int((amount_to_call + 15) * hand_strength_multiplier), player_chips)
            return ActionResponse(action=Action.RAISE, amount=raise_amount)
        else:
            # Large bet, but we have a strong hand, call
            call_amount = min(amount_to_call, player_chips)
            return ActionResponse(action=Action.CALL, amount=call_amount)

    # Medium-strong hands - play moderately aggressive
    elif (
        (has_ace and has_face_card)
        or (is_suited and has_face_card)
        or (is_connected and has_face_card)
        or (hand_type == 1 and community_cards)
    ):
        if amount_to_call == 0:
            # No bet to call, check or small bet
            if random.random() < 0.6:
                return ActionResponse(action=Action.CHECK, amount=0)
            else:
                bet_amount = min(int(10 * hand_strength_multiplier), player_chips)
                return ActionResponse(action=Action.RAISE, amount=bet_amount)
        elif bet_ratio < 0.2:
            # Small bet, call or raise
            if random.random() < 0.7:
                call_amount = min(amount_to_call, player_chips)
                return ActionResponse(action=Action.CALL, amount=call_amount)
            else:
                raise_amount = min(int((amount_to_call + 10) * hand_strength_multiplier), player_chips)
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


async def get_check_call_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
    community_cards: List[Card],
    betting_round: BettingRound,
) -> ActionResponse:
    """
    This type of player will always either check or call.

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :param community_cards: The community cards currently on the table
    :param betting_round: The current betting round
    :return: An ActionResponse object with the action and amount
    """
    if amount_to_call == 0:
        return ActionResponse(action=Action.CHECK, amount=0)
    else:
        return ActionResponse(action=Action.CALL, amount=amount_to_call)


async def get_llm_one_shot_action(
    player: Player,
    amount_to_call: int,
    player_chips: int,
    community_cards: List[Card],
    betting_round: BettingRound,
    model: str = "gpt-4o-mini",
) -> ActionResponse:
    """
    Get action using LLM one-shot

    :param player: The player to get an action for
    :param amount_to_call: The bet amount required in order to stay in the hand
    :param player_chips: The number of chips the player has
    :param community_cards: The community cards currently on the table
    :param betting_round: The current betting round
    :return: An ActionResponse object with the action and amount
    """
    # Build community cards string
    if community_cards:
        community_cards_str = f"Community cards: {hand_to_string(community_cards)}"
    else:
        community_cards_str = "Community cards: None (pre-flop)"

    prompt = dedent(
        f"""# Background
        You're a pro poker player. Given the following game state, your job is to decide what action to take:

        # Game state
        - Betting round: {betting_round.value}
        - Amount of chips needing to be called: {amount_to_call}
        - Your hole cards: {hand_to_string(player.hand)}
        - {community_cards_str}
        - You have {player_chips} chips
        """
    )
    if amount_to_call == 0:
        response = await get_completion_structured(prompt, CheckOrRaise, model=model)
    else:
        response = await get_completion_structured(prompt, CallFoldOrRaise, model=model)

    # Handle case where LLM returns None for amount
    amount = response.amount if response.amount is not None else 0
    return ActionResponse(action=Action(response.action), amount=amount)
