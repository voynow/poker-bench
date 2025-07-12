# Poker Bench

**Evaluate Large Language Models (LLMs) as Texas Hold'em poker strategists with quantitative metrics, cost analytics, and full game simulation.** This project lets you pit different LLMs and AI agents against each other in simulated poker tournaments and analyze their prowess, style, and efficiency.

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [LLM Configuration](#llm-configuration)
- [Metrics and Analysis](#metrics-and-analysis)
- [Advanced Analysis of LLM Usage](#advanced-analysis-of-llm-usage)
- [Customization & Extensibility](#customization--extensibility)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Texas Hold'em Poker Simulation Engine:** Runs realistic full-table poker tournaments with blinds, betting, elimination, and showdowns.
- **Multiple AI Strategies:**
  - *Random*: Baseline player choosing random actions.
  - *Hand-based*: Player using classic hand-evaluation heuristics.
  - *LLM-One-Shot*: LLM chooses action without intermediate reasoning.
  - *LLM-Reasoning*: LLM provides step-by-step rationale and action.
- **LLM Integration:** Supports different OpenAI GPT-4* models. Simple to extend to others.
- **Metrics & Quantitative Performance:** Net chips, volatility, aggression, passivity, and average bet size breakdowns after simulation.
- **LLM Usage Analytics:** Logs and analyzes LLM calls for cost, latency, efficiency, and outlier detection.
- **Highly Modular Design:** Easily add new strategies or swap in models.

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **OpenAI API Key** ([Get one here](https://platform.openai.com/account/api-keys))
- (Recommended) [Poetry](https://python-poetry.org/) or just use pip.

### Installation

Clone the repository:

```
git clone <repo_url>
cd <repo_dir>
```

Install dependencies:

- **With Poetry:**
    ```
    poetry install
    ```
- **With pip:**
    ```
    pip install -r requirements.txt
    ```
    Or manually for key packages:
    ```
    pip install polars pyarrow pydantic tqdm python-dotenv openai
    ```

Set your OpenAI API key:

- Create a `.env` file in the root directory containing:
    ```
    OPENAI_API_KEY=sk-...
    ```

---

### Running Your First Simulation

Launch 100 simulated poker games with default settings:

```
python main.py
```

You'll see progress bars and output metrics. All LLM usage is automatically logged for analysis.

---

## Project Structure

```
.
├── main.py                # Entry point: runs simulations, aggregates stats
├── game.py                # Core Hold'em logic: dealing, bet handling, showdowns
├── player_actions.py      # Different player strategies (random, hand-based, LLM, etc.)
├── constants_and_types.py # All data models, enums, type safety, utilities
├── llm.py                 # LLM interface, logging, and usage tracking
├── metrics.py             # Post-game aggregate analysis and pretty tables
├── analyze_llm_usage.py   # Standalone tool to analyze LLM usage logs
├── llm_usage_log.csv      # (Auto-generated) LLM usage, cost, latency for every call
└── ...
```

#### High-level Architecture

- **main.py**: Orchestrates multi-game runs and prints results.
- **game.py**: Implements card dealing, betting, elimination, showdown logic.
- **player_actions.py**: Defines modular AI/LLM strategies.
- **llm.py**: Handles OpenAI API calls, cost tracking, and logging.
- **metrics.py**: Computes chip/bet/aggression metrics.
- **analyze_llm_usage.py**: Loads `llm_usage_log.csv` and creates an efficiency/cost report.

---

## Usage Examples

### 1. Run a Full Tournament Simulation

Just execute:

```
python main.py
```

- *Configurable*: Change number of games/rounds at the top of `main.py` (`n_games`, `max_rounds`).
- *Default Players*: Two "archetypes" (one-shot, reasoning) * each of three models = 6 LLM-based players.

### 2. (Preview) Sample Metrics Output

After all games, you'll see tables like:

```
-------------------------------
        Total Net Chips        
-------------------------------
one_shot_gpt-4o-mini      10,340 chips
reasoning_gpt-4.1-nano     9,290 chips
...                       ...
-------------------------------
The total net chips across all games

-------------------------------
         Chip Volatility        
-------------------------------
one_shot_gpt-4.1-nano      82 chips
reasoning_gpt-4o-mini     175 chips
...                       ...
-------------------------------
The std dev of chip count across games
```

Metrics include:
- **Net chips**
- **Chip volatility (consistency)**
- **Average bet size**
- **Aggressiveness (% actions as raises)**
- **Passivity (% folds)**

All reported per player type/model.

---

## LLM Configuration

- **Models Supported** (default):  
  - `gpt-4o-mini`
  - `gpt-4.1-mini`
  - `gpt-4.1-nano`
- **To swap/add models:** Edit the `models` list in `setup_players()` in `main.py`.
- **To adjust strategies:** See/add in `player_actions.py`. For example, swap between LLM, random, or custom strategies.
- **LLM API Calls:** All usage is logged (prompt, completion, tokens, cost, latency).

Pricing (see `llm.py`):
```
MODEL_PRICING = {
    "gpt-4o-mini": {"input": $0.15, "output": $0.60} per million tokens,
    ...
}
```

---

## Metrics and Analysis

After the simulation, the following stats are calculated (see `metrics.py`):

- **Total Net Chips:** Which player archetype ended up with the most chips.
- **Chip Volatility:** Standard deviation of chip count per player (lower = more consistent play).
- **Average Bet Size:** Average chips wagered per action.
- **Aggressiveness:** % of actions that are raises.
- **Passivity:** % of actions that are folds.

All shown in readable tabular form for quick comparison.

---

## Advanced Analysis of LLM Usage

Every LLM call during play is logged in `llm_usage_log.csv`. This enables:

### Run Usage Analyzer

```
python analyze_llm_usage.py
```

Features:
- **Total LLM requests, cost, tokens used**
- **Usage and cost breakdown by model and by function**
- **Token/second rates, cost per 1k tokens, average latencies**
- **Top most expensive requests**
- **Outlier detection for high-latency/high-cost calls**
- **Efficient "cost per action" benchmarking for tuning experiments**

**Sample Output:**
```
LLM Usage Analysis Report
========================

Basic Statistics:
- Total Requests: 600
- Date Range: 2024-06-01 to 2024-06-01
- Total Cost: $0.0152
- Total Tokens: 123,456
- Unique Models: 3

Top Models by Cost:
┌──────────────┬───────────────┬───────────┬────────────────────┬─────────────┐
│    model     │ total_cost($) │ ...       │ tokens_per_second  │ ...         │
...
```

---

## Customization & Extensibility

- **Add New Player Archetypes:**  
  Implement a `get_my_strategy_action(...)` function in `player_actions.py`, then add it to `setup_players()` in `main.py`.
- **Add/Swap LLM Models:**  
  Edit the `models` list in `setup_players()`, and make sure their pricing is in `llm.py`.
- **Tune Game Parameters:**  
  Change starting chips, blinds, or game rules in `constants_and_types.py` and `game.py`.
- **Change Metrics:**  
  Add new metrics or visualizations in `metrics.py`.

---

## Contributing

- Pull requests are welcome!
- Please document new strategies, models, or analysis modules clearly.
- For bugs, suggestions, or feature requests, open an issue or contact the maintainer.

---

## License

*(Specify the license here — e.g., MIT, Apache-2.0, etc., if open source.)*

---

## Acknowledgments

- Heavily inspired by classic research in game-playing AI and GTO strategy.
- Uses [OpenAI](https://openai.com/) models and [Polars](https://pola-rs.github.io/polars/) for blazing-fast analytics.

---

**Ready to test your favorite model's poker IQ or investigate the economics of LLM-powered games? Spin up and start experimenting!**