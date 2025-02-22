import unittest
from datetime import datetime, timedelta
import pandas as pd
import pytz
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.trading_system_runner import TradingSystemRunner

class TestTradingSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Get the base project directory
        cls.project_dir = Path(__file__).parent.parent
        cls.data_dir = cls.project_dir / "src/market_data"
        
        # Ensure data directory exists
        if not cls.data_dir.exists() or not any(cls.data_dir.glob("*_hourly.csv")):
            raise unittest.SkipTest("No market data files found. Please run data collection first.")
        
        # Set reference date with timezone
        cls.ny_tz = pytz.timezone('America/New_York')
        cls.reference_date = cls.ny_tz.localize(datetime(2025, 2, 5))
        
        # Create test runner
        cls.runner = TradingSystemRunner(
            data_dir=str(cls.data_dir),
            prompts_dir=str(cls.project_dir / "prompts"),
            results_dir=str(cls.project_dir / "backtest_results"),
            reference_date=cls.reference_date
        )

    def test_forward_testing_period(self):
        """Test that trades can span the full forward testing period"""
        results = self.runner.run_historical_test(
            lookback_days=14,
            forward_days=7
        )
        
        # Check if trades exist
        self.assertTrue(any(results.values()), "No trading results found")
        
        for persona_results in results.values():
            if 'trade_log' in persona_results:
                for trade in persona_results['trade_log']:
                    # Convert string times to timezone-aware datetimes
                    entry_time = pd.to_datetime(trade['entry_time']).tz_localize('America/New_York')
                    exit_time = pd.to_datetime(trade['exit_time']).tz_localize('America/New_York')
                    
                    # Trade duration should be more than 1 hour
                    duration = exit_time - entry_time
                    self.assertGreater(
                        duration,
                        timedelta(hours=1),
                        "Trade duration too short"
                    )
                    
                    # Ensure entry time is at or after reference date
                    self.assertGreaterEqual(
                        entry_time,
                        self.reference_date,
                        "Trade entry before reference date"
                    )
                    
                    # Exit time should not exceed forward testing period
                    max_exit = self.reference_date + timedelta(days=7)
                    self.assertLessEqual(
                        exit_time,
                        max_exit,
                        "Trade extends beyond forward testing period"
                    )

    def test_trade_duration(self):
        """Test that trades are not closed immediately"""
        results = self.runner.run_historical_test(
            lookback_days=14,
            forward_days=7
        )
        
        for persona_results in results.values():
            if 'trade_log' in persona_results:
                for trade in persona_results['trade_log']:
                    # Check entry and exit times are different
                    self.assertNotEqual(
                        trade['entry_time'],
                        trade['exit_time'],
                        "Trade was closed immediately"
                    )
                    
                    # Check entry and exit prices are different
                    self.assertNotEqual(
                        trade['entry_price'],
                        trade['exit_price'],
                        "Entry and exit prices are identical"
                    )

    def test_market_data_processing(self):
        """Test market data processing across multiple days"""
        # Test data loading for a sample of tickers
        sample_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "PYPL", "INTC", "CSCO", "CMCSA", "ADBE", "QCOM", "TXN", "TMUS", "ABNB", "BKNG", "AMD", "SBUX", "INTU", "CHTR", "ISRG", "MDLZ", "GILD", "LRCX", "REGN", "ATVI", "ADI", "AMAT", "MRVL", "ASML", "MRNA", "KLAC", "MU", "MNST", "AVGO", "TEAM", "DXCM", "ILMN", "BIIB", "SNPS", "CDNS", "ALGN", "WDAY", "IDXX", "NXPI", "FTNT", "CTSH", "EA", "VRSK", "PAYX", "ROST", "ODFL", "CPRT", "ADSK", "FAST", "DLTR", "CTAS", "ZM", "PANW", "VRTX", "CRWD", "EBAY", "MCHP", "DDOG", "XEL", "ANSS", "SPLK", "SWKS", "SIRI", "MTCH", "OKTA", "DOCU", "SGEN", "ZS", "ULTA", "CDW", "FANG", "ETSY", "TTWO", "WBA", "LCID", "RIVN", "PCAR", "ORLY", "MAR", "COST", "PDD", "JD", "DASH", "COIN", "LULU", "ROKU", "NET", "TTD", "RBLX", "SOFI", "UPST", "PLTR"]
        start_date = self.reference_date - timedelta(days=14)
        end_date = self.reference_date + timedelta(days=7)
        
        market_data = self.runner._slice_market_data(
            market_data=self.runner.data_collector.get_data_for_analysis(
                tickers=sample_tickers,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                resolution="hourly"
            ),
            start_date=start_date,
            end_date=end_date
        )
        
        for ticker, data in market_data.items():
            # Check data continuity
            self.assertGreater(len(data), 24, f"Less than 24 hours of data for {ticker}")
            
            # Check for required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                self.assertIn(col, data.columns, f"Missing {col} column for {ticker}")
            

if __name__ == '__main__':
    unittest.main()