from datetime import datetime
import pytz
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.trading_system_runner import TradingSystemRunner

# Set reference date with timezone
ny_tz = pytz.timezone('America/New_York')
reference_date = ny_tz.localize(datetime(2025, 2, 5))

# Create runner
runner = TradingSystemRunner(
    data_dir=str(project_root / "src/market_data"),
    prompts_dir=str(project_root / "src/prompts"),
    results_dir=str(project_root / "src/backtest_results"),
    reference_date=reference_date
)

# Run the actual simulation
results = runner.run_historical_test(
    lookback_days=14,
    forward_days=7
)

print("Trading simulation completed!")