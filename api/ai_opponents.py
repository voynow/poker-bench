import random
from typing import Tuple

from game import Player


def get_ai_action(
    player: Player,
    current_bet: int,
    player_chips: int,
) -> Tuple[str, int]:
    if current_bet == 0:
        # No bet to call - can check or bet
        if random.random() < 0.7:
            print(f"   {player.name} decides to CHECK (no bet)")
            return "check", 0
        else:
            bet_amount = min(10, player_chips)
            print(f"   {player.name} decides to BET {bet_amount} chips")
            return "bet", bet_amount
    else:
        # There's a bet to call
        if random.random() < 0.6:
            print(f"   {player.name} decides to CALL {current_bet} chips")
            return "call", current_bet
        else:
            print(f"   {player.name} decides to FOLD")
            return "fold", 0
