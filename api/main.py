import random
from typing import Dict, List, Optional, Tuple

# Card representation: (rank, suit)
Card = Tuple[int, str]
Hand = List[Card]

# Constants
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {rank: i + 2 for i, rank in enumerate(RANKS)}


def create_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    return [(rank_val, suit) for rank_val in range(2, 15) for suit in SUITS]


def deal_cards(deck: List[Card], num_cards: int) -> List[Card]:
    """Deal num_cards from the deck."""
    return [deck.pop() for _ in range(num_cards)]


def rank_to_string(rank: int) -> str:
    """Convert rank number to string."""
    return RANKS[rank - 2]


def card_to_string(card: Card) -> str:
    """Convert card tuple to readable string."""
    rank, suit = card
    return f"{rank_to_string(rank)}{suit}"


def hand_to_string(hand: Hand) -> str:
    """Convert hand to readable string."""
    return " ".join(card_to_string(card) for card in hand)


def best_hand_from_seven(cards: List[Card]) -> Tuple[int, List[int], List[Card]]:
    """Find the best 5-card hand from 7 cards."""
    from itertools import combinations

    best_score = (-1, [])
    best_hand = []

    for combo in combinations(cards, 5):
        hand_type, tiebreakers = evaluate_hand(list(combo))
        score = (hand_type, tiebreakers)
        if score > best_score:
            best_score = score
            best_hand = list(combo)

    return best_score[0], best_score[1], best_hand


def evaluate_hand(hand: Hand) -> Tuple[int, List[int]]:
    """
    Evaluate poker hand strength.
    Returns (hand_type, tiebreaker_values) where higher is better.
    """
    ranks = sorted([card[0] for card in hand], reverse=True)
    suits = [card[1] for card in hand]

    # Count ranks
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), reverse=True)

    # Check for flush
    is_flush = len(set(suits)) == 1

    # Check for straight
    is_straight = False
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
        # Special case: A-2-3-4-5 straight (wheel)
        elif unique_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            unique_ranks = [5, 4, 3, 2, 1]  # Ace low

    # Hand rankings (higher number = better hand)
    if is_straight and is_flush:
        return (8, unique_ranks)  # Straight flush
    elif counts == [4, 1]:
        return (
            7,
            [rank for rank, count in rank_counts.items() if count == 4]
            + [rank for rank, count in rank_counts.items() if count == 1],
        )  # Four of a kind
    elif counts == [3, 2]:
        return (
            6,
            [rank for rank, count in rank_counts.items() if count == 3]
            + [rank for rank, count in rank_counts.items() if count == 2],
        )  # Full house
    elif is_flush:
        return (5, unique_ranks)  # Flush
    elif is_straight:
        return (4, unique_ranks)  # Straight
    elif counts == [3, 1, 1]:
        return (
            3,
            [rank for rank, count in rank_counts.items() if count == 3]
            + sorted(
                [rank for rank, count in rank_counts.items() if count == 1],
                reverse=True,
            ),
        )  # Three of a kind
    elif counts == [2, 2, 1]:
        pairs = sorted(
            [rank for rank, count in rank_counts.items() if count == 2], reverse=True
        )
        kicker = [rank for rank, count in rank_counts.items() if count == 1]
        return (2, pairs + kicker)  # Two pair
    elif counts == [2, 1, 1, 1]:
        pair = [rank for rank, count in rank_counts.items() if count == 2]
        kickers = sorted(
            [rank for rank, count in rank_counts.items() if count == 1], reverse=True
        )
        return (1, pair + kickers)  # One pair
    else:
        return (0, unique_ranks)  # High card


def get_hand_name(hand_type: int) -> str:
    """Get readable name for hand type."""
    names = [
        "High Card",
        "Pair",
        "Two Pair",
        "Three of a Kind",
        "Straight",
        "Flush",
        "Full House",
        "Four of a Kind",
        "Straight Flush",
    ]
    return names[hand_type]


def show_current_hand(hole_cards: List[Card], community_cards: List[Card]) -> None:
    """Show player's current best hand."""
    if len(community_cards) >= 3:
        all_cards = hole_cards + community_cards
        hand_type, tiebreakers, best_hand = best_hand_from_seven(all_cards)
        print(f"Your current hand: {get_hand_name(hand_type)}")
    else:
        print(f"Your hole cards: {hand_to_string(hole_cards)}")


def get_player_action(
    player_name: str, current_bet: int, player_chips: int, pot: int
) -> Tuple[str, int]:
    """Get player action (fold, call, bet/raise)."""
    if player_name == "You":
        print(f"Pot: {pot} | Your chips: {player_chips}")
        while True:
            if current_bet == 0:
                action = input("Action (c)heck, (b)et, (f)old: ").lower().strip()
                if action in ["c", "check"]:
                    return "check", 0
                elif action in ["b", "bet"]:
                    try:
                        amount = int(input("Bet amount: "))
                        if 0 < amount <= player_chips:
                            return "bet", amount
                        else:
                            print(f"Invalid amount. You have {player_chips} chips.")
                    except ValueError:
                        print("Invalid amount.")
                elif action in ["f", "fold"]:
                    return "fold", 0
                else:
                    print("Invalid action.")
            else:
                to_call = current_bet
                action = (
                    input(f"Action (c)all {to_call}, (r)aise, (f)old: ").lower().strip()
                )
                if action in ["c", "call"]:
                    return "call", to_call
                elif action in ["r", "raise"]:
                    try:
                        amount = int(input("Raise to: "))
                        if amount > current_bet and amount <= player_chips:
                            return "raise", amount
                        else:
                            print(
                                f"Invalid raise. Current bet: {current_bet}, Your chips: {player_chips}"
                            )
                    except ValueError:
                        print("Invalid amount.")
                elif action in ["f", "fold"]:
                    return "fold", 0
                else:
                    print("Invalid action.")
    else:
        # Simple AI logic
        if current_bet == 0:
            if random.random() < 0.7:
                return "check", 0
            else:
                return "bet", min(10, player_chips)
        else:
            if random.random() < 0.6:
                return "call", current_bet
            else:
                return "fold", 0


def play_round(num_players: int) -> None:
    """Play a single round of Texas Hold'em."""
    print(f"\n--- Texas Hold'em vs {num_players} players ---")

    # Initialize players with chips
    players = {}
    active_players = set()
    player_chips = {}

    for i in range(num_players + 1):
        name = "You" if i == 0 else f"Player {i}"
        players[name] = []
        active_players.add(name)
        player_chips[name] = 100  # Start with 100 chips

    # Create and shuffle deck
    deck = create_deck()
    random.shuffle(deck)

    # Deal 2 hole cards to each player
    for name in players:
        players[name] = deal_cards(deck, 2)

    print(f"Your hole cards: {hand_to_string(players['You'])}")

    # Community cards
    community_cards = []
    pot = 0
    current_bet = 0

    # Pre-flop betting
    print("\n--- Pre-flop betting ---")
    pot, current_bet, active_players = betting_round(
        active_players, player_chips, pot, current_bet
    )
    print(f"Pot: {pot}")

    if len(active_players) <= 1:
        winner = list(active_players)[0] if active_players else "No one"
        print(f"Winner: {winner} (others folded)")
        return

    # Flop (3 community cards)
    community_cards.extend(deal_cards(deck, 3))
    print(f"\nFlop: {hand_to_string(community_cards)}")
    if "You" in active_players:
        show_current_hand(players["You"], community_cards)
    current_bet = 0
    pot, current_bet, active_players = betting_round(
        active_players, player_chips, pot, current_bet
    )
    print(f"Pot: {pot}")

    if len(active_players) <= 1:
        winner = list(active_players)[0] if active_players else "No one"
        print(f"Winner: {winner} (others folded)")
        return

    # Turn (1 community card)
    community_cards.extend(deal_cards(deck, 1))
    print(f"\nTurn: {hand_to_string(community_cards)}")
    if "You" in active_players:
        show_current_hand(players["You"], community_cards)
    current_bet = 0
    pot, current_bet, active_players = betting_round(
        active_players, player_chips, pot, current_bet
    )
    print(f"Pot: {pot}")

    if len(active_players) <= 1:
        winner = list(active_players)[0] if active_players else "No one"
        print(f"Winner: {winner} (others folded)")
        return

    # River (1 community card)
    community_cards.extend(deal_cards(deck, 1))
    print(f"\nRiver: {hand_to_string(community_cards)}")
    if "You" in active_players:
        show_current_hand(players["You"], community_cards)
    current_bet = 0
    pot, current_bet, active_players = betting_round(
        active_players, player_chips, pot, current_bet
    )
    print(f"Pot: {pot}")

    if len(active_players) <= 1:
        winner = list(active_players)[0] if active_players else "No one"
        print(f"Winner: {winner} (others folded)")
        return

    # Showdown
    print("\n--- Showdown ---")
    best_hands = {}

    for name in active_players:
        all_cards = players[name] + community_cards
        hand_type, tiebreakers, best_hand = best_hand_from_seven(all_cards)
        best_hands[name] = (hand_type, tiebreakers, best_hand)
        print(
            f"{name}: {hand_to_string(players[name])} -> {hand_to_string(best_hand)} ({get_hand_name(hand_type)})"
        )

    # Find winner
    best_score = max(best_hands.values(), key=lambda x: (x[0], x[1]))
    winners = [
        name for name, score in best_hands.items() if score[:2] == best_score[:2]
    ]

    print(f"\nWinner: {', '.join(winners)}")
    if "You" in winners:
        print("You won!")
    else:
        print("You lost.")


def betting_round(
    active_players: set, player_chips: dict, pot: int, current_bet: int
) -> Tuple[int, int, set]:
    """Handle a betting round."""
    players_to_act = list(active_players)
    player_bets = {name: 0 for name in active_players}

    while len(players_to_act) > 0:
        player = players_to_act.pop(0)

        if player not in active_players:
            continue

        to_call = current_bet - player_bets[player]

        if to_call >= player_chips[player]:
            # Player is all-in
            action, amount = "call", player_chips[player]
        else:
            action, amount = get_player_action(
                player, to_call, player_chips[player], pot
            )

        if action == "fold":
            active_players.remove(player)
            print(f"{player} folds")
        elif action == "check":
            print(f"{player} checks")
        elif action == "call":
            player_bets[player] += amount
            player_chips[player] -= amount
            pot += amount
            if player == "You":
                print(f"You call {amount}")
            else:
                print(f"{player} calls {amount}")
        elif action in ["bet", "raise"]:
            player_bets[player] += amount
            player_chips[player] -= amount
            pot += amount
            current_bet = player_bets[player]
            if player == "You":
                print(f"You {action} to {current_bet}")
            else:
                print(f"{player} {action}s to {current_bet}")

            # Add other players back to act if there was a raise
            for other_player in active_players:
                if other_player != player and other_player not in players_to_act:
                    if player_bets[other_player] < current_bet:
                        players_to_act.append(other_player)

    return pot, current_bet, active_players


def main():
    """Main game loop."""
    print("Let's Play Texas Hold'em!")
    play_round(5)


if __name__ == "__main__":
    main()
