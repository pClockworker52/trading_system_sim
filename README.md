# Algorithmic Trading System

A sophisticated trading system implementation with algorithmic trading capabilities, backtesting framework, and multiple agent personas.

## Overview

This system enables:

1. **Multiple Trading Personas**: Test different trading strategies via customizable prompt-based agents
2. **Historical Backtesting**: Evaluate trading decisions against real market data
3. **Performance Analysis**: Generate detailed reports on trading performance
4. **Data Collection**: Automated market data collection for NASDAQ stocks

## Key Features

- **Prompt-Based Agents**: Each trading agent uses a different persona defined through prompts
- **Enhanced Backtesting**: Realistic simulation including transaction fees and time-based exits
- **Visualization Tools**: Generate HTML reports and dashboards for performance analysis
- **Extensible Architecture**: Easily add new trading personas and strategies

## Quick Start

### Prerequisites

- Python 3.8+
- Local Llama2 model running on http://localhost:11434 (or modify the API endpoint in `sophisticated_trader_agent.py`)
- Required packages (see requirements.txt)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trading-system.git
   cd trading-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have a local LLM API running for trading decisions, or modify the code to use a different API.

### Usage

1. Collect market data (if not already present):
   ```bash
   python -m src.market_data_collection_system
   ```

2. Create trading personas in the `prompts/` directory (examples provided)

3. Run a historical backtest:
   ```bash
   python main.py
   ```

4. View the results in the generated HTML report

## Project Structure

```
trading_system/
│
├── main.py                            # Entry point of the application
│
├── src/                               # Source code
│   ├── enhanced_algo_test.py          # Advanced algorithm testing
│   ├── market_data_collection_system.py # Market data collection
│   ├── sophisticated_trader_agent.py  # Trading agent implementation
│   ├── trading_system_runner.py       # System execution logic
│   │
│   ├── utilities/                     # Utility functions
│   │   └── json_to_html.py           # JSON to HTML converter
│   │
│   ├── validators/                    # Input validation
│   │   └── llm_response_validator.py  # LLM response validation
│   │
│   └── visualization/                # Visualization components
│       └── trading_dashboard.jsx     # React dashboard
│
├── tests/                            # Test suite
│   └── test_trading_system.py       # System tests
│
└── data/                            # Market data (not tracked in git)
```

## Trading Personas

Trading personas are defined in text files in the `prompts/` directory. Each persona represents a different trading style or strategy. You can create custom personas by following the format in the existing examples.

## Running Tests

Run the test suite to ensure everything is working correctly:

```bash
python -m unittest discover tests/
```

## Visualizing Results

After running a backtest, the system generates:

1. JSON files with detailed trading results
2. HTML reports with visualizations
3. Log files with system events

The HTML reports will automatically open in your default browser.

## Customization

- **Adding new personas**: Create new text files in the `prompts/` directory
- **Modifying backtesting parameters**: Edit the settings in `main.py`
- **Adding new visualization**: Modify the `json_to_html.py` file or the React components


## License

[Specify your license here]

## Acknowledgments

- yfinance for market data access
- All contributors to the project
