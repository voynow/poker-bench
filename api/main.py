import random
import time
from enum import Enum
from itertools import combinations
from typing import List, Tuple

from pydantic import BaseModel


class Suit(Enum):
    """Represent the four suits in a standard deck."""

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


Card = Tuple[int, Suit]
Hand = List[Card]


def hand_to_string(hand: Hand) -> str:
    """Convert hand to readable string."""
    return " ".join(f"{RANKS[rank - 2]}{suit.value}" for rank, suit in hand)


class Player(BaseModel):
    name: str
    chips: int
    hand: Hand

    def __hash__(self):
        """Make Player hashable so it can be used in sets and as dict keys."""
        return hash(self.name)


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {rank: i + 2 for i, rank in enumerate(RANKS)}


HAND_NAMES = [
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


def print_card_visual(card: Card) -> str:
    """Return a visual representation of a card."""
    rank, suit = card
    rank_str = RANKS[rank - 2]
    return f"{rank_str}{suit.value}"


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


def print_showdown_results(player_hands: dict, community_cards: List[Card]):
    """Print showdown results in a formatted table."""
    print("\n" + "=" * 60)
    print("Showdown")
    print("=" * 60)
    print(f"   {hand_to_string(community_cards)}")
    print("\nHand rankings:")
    print("-" * 50)

    # Sort players by hand strength for better display
    sorted_hands = sorted(player_hands.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)

    for i, (player, (hand_type, tiebreakers, best_hand)) in enumerate(sorted_hands):
        hole_cards = "  ".join(print_card_visual(card) for card in player.hand)
        best_cards = "  ".join(print_card_visual(card) for card in best_hand)
        hand_name = HAND_NAMES[hand_type]

        rank_indicator = "1st" if i == 0 else "2nd" if i == 1 else "3rd" if i == 2 else "  "

        if player.name == "You":
            print(f"  {rank_indicator}  You:")
        else:
            print(f"  {rank_indicator}   {player.name}:")

        print(f"      Hole cards: {hole_cards}")
        print(f"      Best hand:  {best_cards}")
        print(f"      Hand type:  {hand_name}")
        print()

    print("=" * 60)


def create_deck() -> List[Card]:
    """
    Create a standard 52-card deck in order of suits and ranks

    :return: List[Card]: A list of cards in the deck
    """
    return [(rank_val, suit) for rank_val in range(2, 15) for suit in Suit]


def deal_cards(deck: List[Card], num_cards: int) -> List[Card]:
    """
    Deal num_cards from the deck

    :param deck: List[Card]: The deck of cards
    :param num_cards: int: The number of cards to deal
    :return: List[Card]: A list of cards dealt from the deck
    """
    return [deck.pop() for _ in range(num_cards)]


def best_hand_from_seven(cards: List[Card]) -> Tuple[int, List[int], List[Card]]:
    """
    Find the best 5-card hand from 7 cards

    :param cards: List[Card]: The cards to evaluate
    :return: Tuple[int, List[int], List[Card]]: The best hand
    """

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
        )
    elif counts == [2, 2, 1]:
        pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
        kicker = [rank for rank, count in rank_counts.items() if count == 1]
        return (2, pairs + kicker)
    elif counts == [2, 1, 1, 1]:
        pair = [rank for rank, count in rank_counts.items() if count == 2]
        kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
        return (1, pair + kickers)  # One pair
    else:
        return (0, unique_ranks)  # High card


def get_player_action(player: Player, current_bet: int, player_chips: int, pot: int) -> Tuple[str, int]:
    """
    Get player action (fold, call, bet/raise)

    :param player: Player: The player making the action
    :param current_bet: int: The current bet
    :param player_chips: int: The number of chips the player has
    :param pot: int: The current pot
    """
    if player.name == "You":
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
                    return "check", 0
                elif action in ["b", "bet"]:
                    try:
                        amount = int(input(f"   Enter bet amount (1-{player_chips}): "))
                        if 0 < amount <= player_chips:
                            print(f"You bet {amount} chips")
                            return "bet", amount
                        else:
                            print(f"Invalid amount. Must be between 1 and {player_chips}")
                    except ValueError:
                        print("Please enter a valid number")
                elif action in ["f", "fold"]:
                    print("You chose to FOLD (give up your hand)")
                    return "fold", 0
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
                    return "call", to_call
                elif action in ["r", "raise"]:
                    print(f"You chose to RAISE. Current bet is {current_bet}")
                    try:
                        amount = int(input(f"   Enter your total bet (minimum {current_bet + 1}): "))
                        if amount > current_bet and amount <= player_chips:
                            print(f"You raise to {amount} chips (raising by {amount - current_bet})")
                            return "raise", amount
                        else:
                            print(f"Invalid raise. Must be between {current_bet + 1} and {player_chips}")
                    except ValueError:
                        print("Please enter a valid number")
                elif action in ["f", "fold"]:
                    print("You chose to FOLD (give up your hand)")
                    return "fold", 0
                else:
                    print("Invalid choice. Please enter 'c', 'r', or 'f'")
    else:
        # Simple AI logic with more verbose output
        if current_bet == 0:
            if random.random() < 0.7:
                print(f"   {player.name} decides to CHECK (no bet)")
                return "check", 0
            else:
                bet_amount = min(10, player_chips)
                print(f"   {player.name} decides to BET {bet_amount} chips")
                return "bet", bet_amount
        else:
            if random.random() < 0.6:
                print(f"   {player.name} decides to CALL {current_bet} chips")
                return "call", current_bet
            else:
                print(f"   {player.name} decides to FOLD")
                return "fold", 0


def betting_round(
    active_players: set[Player],
    pot: int,
    current_bet: int,
    player_bets: dict = None,
) -> Tuple[int, int, set]:
    """
    Handle a betting round.

    :param active_players: set: The players that are still in the game
    :param players: List[Player]: The players in the game
    :param pot: int: The current pot
    :param current_bet: int: The current bet
    :param player_bets: dict: Optional existing bets from players (for blinds)
    """
    players_to_act = list(active_players)
    if player_bets is None:
        player_bets = {player: 0 for player in active_players}
    else:
        # Make a copy to avoid modifying the original
        player_bets = player_bets.copy()

    print(f"\nPlayers remaining: {len(active_players)}")
    print(f"Current highest bet: {current_bet} chips")

    while len(players_to_act) > 0:
        player = players_to_act.pop(0)

        if player not in active_players:
            continue

        to_call = current_bet - player_bets[player]

        if to_call >= player.chips:
            # Player is all-in
            action, amount = "call", player.chips
            print(f"💥 {player.name} is ALL-IN with {amount} chips!")
        else:
            action, amount = get_player_action(player, to_call, player.chips, pot)
            time.sleep(1)

        if action == "fold":
            active_players.remove(player)
            if len(active_players) == 1:
                print("🏆 Only one player remains - betting ends!")
                break
        elif action == "check":
            pass
        elif action == "call":
            player_bets[player] += amount
            player.chips -= amount
            pot += amount
        elif action in ["bet", "raise"]:
            old_bet = current_bet
            player_bets[player] += amount
            player.chips -= amount
            pot += amount
            current_bet = player_bets[player]

            if action == "bet":
                pass
            else:
                raise_amount = current_bet - old_bet
                print(f"🔥 {player.name} raises by {raise_amount} chips to {current_bet} total (pot now: {pot})")

            # Add other players back to act if there was a raise
            players_added_back = 0
            for other_player in active_players:
                if other_player != player and other_player not in players_to_act:
                    if player_bets[other_player] < current_bet:
                        players_to_act.append(other_player)
                        players_added_back += 1

            if players_added_back > 0:
                print(f"{players_added_back} players must now act on the {'bet' if action == 'bet' else 'raise'}")

    remaining_players = len(active_players)
    print("\nBetting round complete")
    print(f"   Players still in hand: {remaining_players}")
    print(f"   Final pot size: {pot} chips")

    return pot, current_bet, active_players


def play_round(num_opponents: int):
    """
    Play a single round of Texas Hold'em

    :param num_opponents: int: The number of opponents
    """
    print(f"Starting a new hand against {num_opponents} AI opponents\n")

    # Create players
    players: List[Player] = []
    active_players: set[Player] = set()

    # Create human player
    human_player = Player(name="You", chips=1000, hand=[])
    players.append(human_player)
    active_players.add(human_player)

    # Create AI opponents
    for i in range(num_opponents):
        ai_player = Player(name=f"Player {i + 1}", chips=1000, hand=[])
        players.append(ai_player)
        active_players.add(ai_player)

    deck = create_deck()
    random.shuffle(deck)

    for _ in range(2):
        for player in players:
            player.hand.append(deck.pop())

    pot = 0
    small_blind = 5
    big_blind = 10
    current_bet = big_blind

    # initialize blinds by rotating players
    rotate_index = random.randint(0, len(players) - 1)
    for _ in range(rotate_index):
        players.append(players.pop(0))
    small_blind_player = players[0]
    big_blind_player = players[1]

    print(f"Small blind: {small_blind_player.name} must bet {small_blind} chips")
    print(f"Big blind: {big_blind_player.name} must bet {big_blind} chips")

    small_blind_player.chips -= small_blind
    big_blind_player.chips -= big_blind
    pot += small_blind + big_blind

    # Pre-flop betting round
    print_betting_phase("Pre-flop")

    if len(active_players) > 1:
        blind_bets = {player: 0 for player in active_players}
        blind_bets[small_blind_player] = small_blind
        blind_bets[big_blind_player] = big_blind

        pot, current_bet, active_players = betting_round(active_players, pot, current_bet, blind_bets)
        current_bet = 0

    # Deal flop (3 community cards)
    community_cards = []
    if len(active_players) > 1:
        deck.pop()  # Burn card
        for _ in range(3):
            community_cards.append(deck.pop())
        print_betting_phase("Flop", community_cards)
        pot, current_bet, active_players = betting_round(active_players, pot, current_bet)
        current_bet = 0

    # Deal turn (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        print_betting_phase("Turn", community_cards)
        pot, current_bet, active_players = betting_round(active_players, pot, current_bet)
        current_bet = 0

    # Deal river (1 community card)
    if len(active_players) > 1:
        deck.pop()  # Burn card
        community_cards.append(deck.pop())
        print_betting_phase("River", community_cards)
        pot, current_bet, active_players = betting_round(active_players, pot, current_bet)

    if len(active_players) == 1:
        winner = list(active_players)[0]
        print("\n" + "=" * 60)
        print("Hand Over!")
        print("=" * 60)
        print(f"🎉 {winner.name} wins {pot} chips")
        winner.chips += pot
    else:
        player_hands = {}
        for player in active_players:
            all_cards = player.hand + community_cards
            hand_type, tiebreakers, best_hand = best_hand_from_seven(all_cards)
            player_hands[player] = (hand_type, tiebreakers, best_hand)

        print_showdown_results(player_hands, community_cards)

        best_score = max(player_hands.values(), key=lambda x: (x[0], x[1]))
        winners = [
            player
            for player, hand_data in player_hands.items()
            if (hand_data[0], hand_data[1]) == (best_score[0], best_score[1])
        ]

        if len(winners) == 1:
            winner = winners[0]
            print(f"\n🎉 {winner.name} wins {pot} chips!")
            print(f"🏆 Winning hand: {HAND_NAMES[best_score[0]]}")
            winner.chips += pot
        else:
            # Split pot among winners
            split_amount = pot // len(winners)
            winner_names = [w.name for w in winners]
            print("\n🤝 Tie game: pot split!")
            print(f"🏆 Winners: {', '.join(winner_names)}")
            print(f"💰 Each winner gets {split_amount} chips")
            for winner in winners:
                winner.chips += split_amount

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


if __name__ == "__main__":
    play_round(5)
