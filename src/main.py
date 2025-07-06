from typing import Dict, List, Tuple

from constants_and_types import HAND_NAMES, NUM_OPPONENTS, Card, Player, hand_to_string
from game import (
    apply_blinds,
    determine_winners,
    distribute_winnings,
    get_winners_from_hands,
    print_card_visual,
    process_betting_action,
    setup_players,
    setup_round,
)
from player_actions import Action, ActionResponse, get_action_router


def print_betting_phase(phase: str, cards: List[Card] = None):
    """Print the start of a betting phase."""
    print("\n" + "=" * 60)
    print(f"{phase} betting round")
    print("=" * 60)
    if cards:
        if phase.lower() == "flop":
            print("   First three community cards revealed!")
            print(f"   {hand_to_string(cards)}")
        elif phase.lower() == "turn":
            print("   Fourth community card revealed!")
            print(f"   {hand_to_string(cards)}")
        elif phase.lower() == "river":
            print("   Final community card revealed!")
            print(f"   {hand_to_string(cards)}")


def print_showdown_results(player_hands: Dict[Player, Tuple[int, List[int]]], community_cards: List[Card]):
    """Print showdown results in a formatted table."""
    print("\n" + "=" * 60)
    print("Showdown")
    print("=" * 60)
    print(f"   {hand_to_string(community_cards)}")
    print("\nHand rankings:")
    print("-" * 50)

    # Sort players by hand strength for better display
    sorted_hands = sorted(player_hands.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)

    for i, (player, (hand_type, tiebreakers)) in enumerate(sorted_hands):
        hole_cards = "  ".join(print_card_visual(card) for card in player.hand)
        hand_name = HAND_NAMES[hand_type]

        rank_indicator = "1st" if i == 0 else "2nd" if i == 1 else "3rd" if i == 2 else "  "

        if player.name == "You":
            print(f"  {rank_indicator}  You:")
        else:
            print(f"  {rank_indicator}   {player.name}:")

        print(f"      Hole cards: {hole_cards}")
        print(f"      Hand type:  {hand_name}")
        print()

    print("=" * 60)


def betting_round(
    active_players: List[Player],
    pot: int,
    current_bet: int,
    blinds: Dict[Player, int] = None,
) -> Tuple[int, int, List[Player]]:
    """Handle a betting round with both human and AI players."""
    players_to_act = list(active_players)
    player_bets = blinds.copy() if blinds else {player: 0 for player in active_players}

    print(f"\nPlayers remaining (in order): {', '.join([player.name for player in active_players])}")

    while len(players_to_act) > 0:
        player = players_to_act.pop(0)

        if player not in active_players:
            continue

        to_call = current_bet - player_bets[player]

        if to_call >= player.chips:
            # Player is all-in
            action_response = ActionResponse(action=Action.CALL, amount=player.chips)
        else:
            action_response = get_action_router(player, to_call, player.chips)

        # Process the action using game logic
        pot, current_bet, was_raise = process_betting_action(
            player, action_response.action, action_response.amount, player_bets, pot, current_bet, active_players
        )

        # If there was a raise, add other players back to act
        if was_raise:
            for other_player in active_players:
                if other_player != player and other_player not in players_to_act:
                    # Add players who haven't matched the new current bet
                    if player_bets[other_player] < current_bet:
                        players_to_act.append(other_player)

        # Check if only one player remains
        if len(active_players) == 1:
            break

    remaining_players = len(active_players)
    print("\nBetting round complete")
    print(f"   Players still in hand: {remaining_players}")
    print(f"   Final pot size: {pot} chips")

    return pot, current_bet, active_players


def play_round(players: List[Player]):
    """Play a single round of Texas Hold'em."""
    deck = setup_round(players)

    # Apply blinds
    pot, small_blind_player, big_blind_player = apply_blinds(players)
    small_blind, big_blind = 5, 10
    current_bet = big_blind

    print(f"Small blind: {small_blind_player.name} must bet {small_blind} chips")
    print(f"Big blind: {big_blind_player.name} must bet {big_blind} chips")

    # Pre-flop: rotate so action starts with player to left of big blind
    active_players = players[2:] + players[:2]  # Move first 2 players to end

    # Pre-flop betting round
    print_betting_phase("Pre-flop")

    if len(active_players) > 1:
        blind_bets = {player: 0 for player in active_players}
        blind_bets[small_blind_player] = small_blind
        blind_bets[big_blind_player] = big_blind

        pot, current_bet, active_players = betting_round(
            active_players=active_players, pot=pot, current_bet=current_bet, blinds=blind_bets
        )
        current_bet = 0

    # Post-flop: put small blind first (if still active)
    if len(active_players) > 1 and small_blind_player in active_players:
        sb_idx = active_players.index(small_blind_player)
        active_players = active_players[sb_idx:] + active_players[:sb_idx]

    # Deal flop (3 community cards)
    community_cards = []
    if len(active_players) > 1:
        deck.pop()  # Burn card
        for _ in range(3):
            community_cards.append(deck.pop())
        print_betting_phase("Flop", community_cards)
        pot, current_bet, active_players = betting_round(
            active_players=active_players, pot=pot, current_bet=current_bet
        )
        current_bet = 0

    # Deal turn (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        print_betting_phase("Turn", community_cards)
        pot, current_bet, active_players = betting_round(
            active_players=active_players, pot=pot, current_bet=current_bet
        )
        current_bet = 0

    # Deal river (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        print_betting_phase("River", community_cards)
        pot, current_bet, active_players = betting_round(
            active_players=active_players, pot=pot, current_bet=current_bet
        )

    # Determine winner(s)
    if len(active_players) == 1:
        winner = active_players[0]
        print("\n" + "=" * 60)
        print("Hand Over!")
        print("=" * 60)
        print(f"🎉 {winner.name} wins {pot} chips")
        winner.chips += pot
    else:
        # Showdown
        player_hands = determine_winners(active_players, community_cards)
        print_showdown_results(player_hands, community_cards)

        winners = get_winners_from_hands(player_hands)
        winnings_per_player = distribute_winnings(winners, pot)

        if len(winners) == 1:
            winner = winners[0]
            print(f"\n🎉 {winner.name} wins {pot} chips!")
            best_hand_type = player_hands[winner][0]
            print(f"🏆 Winning hand: {HAND_NAMES[best_hand_type]}")
        else:
            # Split pot among winners
            winner_names = [w.name for w in winners]
            print("\n🤝 Tie game: pot split!")
            print(f"🏆 Winners: {', '.join(winner_names)}")
            print(f"💰 Each winner gets {winnings_per_player} chips")

    # Show final chip counts
    print("\n" + "=" * 60)
    print("Final chip counts")
    print("=" * 60)
    for player in players:
        change = player.chips - 1000
        if change > 0:
            change_str = f"(+{change} 📈)"
        elif change < 0:
            change_str = f"({change} 📉)"
        else:
            change_str = "(even 📊)"

        if player.name == "You":
            print(f"    {player.name:<12} {player.chips:>4} chips {change_str}")
        else:
            print(f"    {player.name:<12} {player.chips:>4} chips {change_str}")
    print("=" * 60)


def main():
    """
    Play N rounds of Texas Hold'em
    """
    players = setup_players(NUM_OPPONENTS + 1)
    round_count = 0
    while True:
        play_round(players)
        play_again = input("Play again? (Y/n): ")
        if play_again.lower() in ["n", "no"]:
            break
        round_count += 1

    user = next(p for p in players if p.name == "You")
    if user.chips > 1000:
        print(f"Thanks for playing! You played {round_count} rounds and won {user.chips - 1000} chips")
    else:
        print(f"Thanks for playing! You played {round_count} rounds and lost {1000 - user.chips} chips")


if __name__ == "__main__":
    main()
