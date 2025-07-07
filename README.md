# Texas Hold'em Poker AI Simulator

An **AI-driven Texas Hold'em Poker simulator** for benchmarking strategy-based vs. random agents in simulated tournaments. Runs hundreds of games between AI players, tracks elimination and chip stacks, and reports win rates for different play styles. Great for experimenting with AI, probability, or game theory!

---

## Features

- **Simulate Texas Hold'em Poker among AI opponents**
    - Fully automated game loop and rules
    - Handles deal, betting rounds, all-in, eliminations, and showdown
- **Multiple strategies supported**
    - Strategic ("hand strength-based") bots
    - Random-decision bots
- **Poker mechanics implemented**
    - Blinds, raises, calls, folds, all-in scenarios
    - Hand evaluation, winner determination
    - Pot splitting among ties
- **Tournament play**
    - Multiple round elimination and chip tracking
    - Statistical output: win rates, rounds played, player rankings
- **Extensible AI plug-in system**
    - Add your own Python function as a player strategy

---

## Installation & Setup

**Requirements:**
- Python **3.13** or higher
- [UV](https://docs.astral.sh/uv/) package manager

**Install UV (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install dependencies:**
```bash
uv sync
```

**Run without installation:**
```bash
uv run python src/main.py
```

---

## Quick Start

Run a full tournament simulation between a strategic AI and 4 random opponents:

```bash
uv run python src/main.py
```

**Sample output:**
```
Strategic player won 67.0% of games
```
(The exact percentage will vary per run.)

By default, 100 tournaments are simulated, with detailed statistics collected internally (customize in `main.py`).

---

## How it Works

**Architecture Overview:**

- `main.py`  
    - Tournament supervisor: loops over games, eliminates players, collects stats
- `game.py`  
    - Core poker logic: deck creation, dealing, betting logic, all-in, hand evaluation, pot split rules
- `constants_and_types.py`  
    - Shared constants, type definitions (cards, suits, players, actions)
- `player_actions.py`  
    - AI strategy implementations:
        - `get_random_action`
        - `get_hand_strength_based_action`
- **Game Loop:**
    - Initialize N players (1 "Strategic", N-1 "Random")
    - Repeat:  
        - Deal hands & community cards per Texas Hold'em rules  
        - Run betting rounds (pre-flop, flop, turn, river)  
        - Eliminate broke players  
        - Continue until one winner left or round max reached  
    - Log strategy of winner each game; summarize at end

### AI Strategies & Plug-ins

Each player is controlled by their own "action function" with signature:
```python
def action_func(player, amount_to_call, player_chips) -> ActionResponse
```

- **Random Example:**  
  See `get_random_action` in `player_actions.py`
- **Strategic Example:**  
  See `get_hand_strength_based_action` in `player_actions.py`

To add a new strategy, implement your function and assign it to a Player's `action_func`.

---

## Extending / Customizing

Want to experiment with new AI strategies?  
Just write a new function like so:

```python
def my_custom_ai(player, amount_to_call, player_chips):
    # ...Evaluate hand, stack, table position, etc...
    return ActionResponse(action=Action.RAISE, amount=20)
```
Then, in `setup_players()` (see `main.py`), assign your function to a Player:
```python
Player(name="My AI", chips=1000, hand=[], action_func=my_custom_ai)
```

For reference, check out:
- `get_random_action` in `player_actions.py`
- `get_hand_strength_based_action` in `player_actions.py`

---

## Testing

- **No formal test suite yet.**
- To add: unit tests for hand evaluation and winner determination.
- **Run simulations** (`uv run python src/main.py`) to validate statistical outputs.

TODO:  
- Integrate tests (e.g. [pytest](https://docs.pytest.org/)), especially for hand evaluation edge cases.
- Add sample hands and check that winner logic is robust.

---

## Contributing

Contributions are very welcome!  
- Fork this repo
- Add your own AI in `player_actions.py` or new file
- Open a pull request describing your strategy or code improvement
- Suggest new configuration options, bug fixes, or documentation improvements

---

## License

**[TODO: Add license, e.g. MIT, Apache 2.0, etc.]**

---

## Contact / Credits

Project by [Your Name Here].  
Questions, suggestions, or collaboration? [Link or email here]

---

**Enjoy simulating Poker AI battles! Try writing your own agent and see how it stacks up—pull requests welcome!**