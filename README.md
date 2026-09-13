# Sports Lot Optimiser

## Problem
Sports turf arenas lose revenue because weekday afternoon slots remain vacant. Blindly discounting all slots is not optimal. 

## Solution
An agentic decision system that intelligently evaluates vacant slots based on historical fill rate, remaining lead time, and operational margins. It determines whether to intervene and offers sensible discounts mapped to specific customer segments.

## Architecture
- **UI:** Streamlit
- **Logic:** Deterministic Python Decision Engine
- **Data:** CSV-based synthetic data (No database required)

## Tech Stack
- Python 3.11
- Streamlit
- Pandas
- Pytest

## How to run
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Decision logic
The core engine (`src/engine.py`) determines risk based on `historical_fill_rate` and `lead_time_hours`. Depending on the available `margin_pct`, it decides whether to offer a discount (and how much) and pairs it with an appropriate customer segment for outreach.

## Dataset
- `slots.csv`: A synthetic mixture of obvious 'no action' slots, desperate slots, and ambiguous middle scenarios.
- `segments.csv`: Distinct customer profiles mapped to sports.

## Demo flow
1. Show an obviously fine slot that requires no action.
2. Show an ambiguous slot and demonstrate the tradeoff reasoning.
3. Run All slots and visualize the batch table.
4. Show Before/After status updates in the underlying dataset.

## Team Contribution
- **Person A:** Datasets (`slots.csv`, `segments.csv`)
- **Person B:** Decision engine (`engine.py`, `test_engine.py`)
- **Person C:** Streamlit UI (`app.py`)
- **Person D:** Messaging & Integration (`messaging.py`, `data_loader.py`)
