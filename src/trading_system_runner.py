from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import json
import pandas as pd
import webbrowser
import os

# Update imports to use correct package structure
from src.sophisticated_trader_agent import SophisticatedTrader
from src.market_data_collection_system import MarketDataCollector
from src.enhanced_algo_test import BacktestFramework
from src.utilities.json_to_html import convert_json_to_html

class TradingSystemRunner:
    def __init__(
        self,
        data_dir: str = "market_data",
        prompts_dir: str = "prompts",
        results_dir: str = "backtest_results",
        reference_date: datetime = None
    ):
        self.data_dir = Path(data_dir)
        self.prompts_dir = Path(prompts_dir)
        self.results_dir = Path(results_dir)
        self.reference_date = reference_date or datetime.now()
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.results_dir / "trading_system.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MarketDataCollector(str(self.data_dir))
        self.backtest_framework = BacktestFramework(
            data_dir=str(self.data_dir),
            reference_date=self.reference_date
        )
        
    def _slice_market_data(
        self,
        market_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Slice market data for a specific time period with validation."""
        if not market_data:
            raise ValueError("No market data provided")
            
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            raise ValueError("start_date and end_date must be datetime objects")
            
        if end_date <= start_date:
            raise ValueError("end_date must be after start_date")
            
        sliced_data = {}
        
        for ticker, df in market_data.items():
            if df.empty:
                continue
                
            # Ensure required columns exist
            required_cols = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns for {ticker}: {missing_cols}")
                
            # Convert DataFrame datetime to timezone-aware if it isn't already
            if df['Datetime'].dt.tz is None:
                df['Datetime'] = df['Datetime'].dt.tz_localize('America/New_York')
                
            # Check for sufficient data
            mask = (df['Datetime'] >= start_date) & (df['Datetime'] < end_date)
            filtered_df = df[mask].copy()
            
            if len(filtered_df) < 10:  # Minimum data requirement
                print(f"Warning: Insufficient data points for {ticker}")
                continue
                
            sliced_data[ticker] = filtered_df
            
        if not sliced_data:
            raise ValueError("No valid data after filtering")
            
        return sliced_data

    def _test_single_persona(
        self,
        persona_file: Path,
        decision_data: Dict[str, pd.DataFrame],
        validation_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Test a single trading persona with historical data."""
        trader = SophisticatedTrader(str(persona_file.name))
        
        try:
            # Get data request from trader
            self.logger.info(f"Getting data request for {persona_file.name}")
            data_request = trader.request_data()
            requested_tickers = [
                ticker for ticker in data_request["tickers"]
                if ticker in decision_data
            ]
            
            if not requested_tickers:
                raise ValueError("No requested tickers found in historical data")
            
            # Get trading decision based on decision period data
            self.logger.info(f"Getting trading decision for {persona_file.name}")
            decision = trader.analyze_and_trade(decision_data, requested_tickers)
            decision['persona'] = persona_file.stem  # Add persona name to decision
            self.logger.info(f"Got trading decision: {decision}")
            
            agent_responses = [decision]
            
            # Run backtest using validation period data
            self.logger.info(f"Running backtest for {persona_file.name}")
            metrics, trades = self.backtest_framework.run_backtest(
                market_data=validation_data,
                agent_responses=agent_responses
            )
            
            # Generate report
            self.logger.info(f"Generating report for {persona_file.name}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.results_dir / f"{persona_file.stem}_{timestamp}"
            report = self.backtest_framework.generate_report(str(report_dir))
            
            result = json.loads(report)
            self.logger.info(f"Test results for {persona_file.name}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _test_single_persona for {persona_file.name}: {str(e)}")
            raise

    def _save_consolidated_results(self, all_results: Dict[str, Any]) -> str:
        """Save consolidated results from all personas and return the HTML report path."""
        if not all_results:
            self.logger.warning("No results to save!")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract key metrics for comparison
        comparison = {}
        trades_list = []
        
        for persona, results in all_results.items():
            if not results:
                continue
                
            if 'performance_metrics' in results:
                metrics = results['performance_metrics']
                comparison[persona] = {
                    'win_rate': metrics.get('win_rate', 0),
                    'avg_return': metrics.get('avg_return', 0),
                    'max_loss': metrics.get('max_loss', 0),
                    'max_gain': metrics.get('max_gain', 0)
                }
                
            # Collect trading decisions
            if 'trade_log' in results:
                for trade in results['trade_log']:
                    trade['persona'] = persona
                    trades_list.append(trade)
        
        if comparison:
            # Save comparison report
            comparison_file = self.results_dir / f"persona_comparison_{timestamp}.json"
            with open(comparison_file, 'w') as f:
                json.dump(comparison, indent=2, fp=f)
            self.logger.info(f"Saved comparison to {comparison_file}")
        
        if trades_list:
            # Save trades
            trades_file = self.results_dir / f"trading_decisions_{timestamp}.json"
            with open(trades_file, 'w') as f:
                json.dump(trades_list, indent=2, fp=f)
            self.logger.info(f"Saved trades to {trades_file}")
            
            # Generate HTML report
            try:
                html_report_path = convert_json_to_html(
                    str(trades_file),
                    str(self.results_dir / "html_reports")
                )
                self.logger.info(f"HTML report generated at: {html_report_path}")
                return html_report_path
            except Exception as e:
                self.logger.error(f"Error generating HTML report: {str(e)}")
                
        return None

    def run_historical_test(
        self,
        lookback_days: int = 14,
        forward_days: int = 7
    ) -> Dict[str, Any]:
        """Run system test using historical data from reference date."""
        self.logger.info(f"Starting historical test for reference date: {self.reference_date}")
        
        # Calculate test period dates
        data_start = self.reference_date - timedelta(days=lookback_days)
        data_end = self.reference_date + timedelta(days=forward_days)
        
        # Get historical market data
        self.logger.info("Collecting historical market data...")
        market_data = self.data_collector.get_historical_data(
            start_date=data_start,
            end_date=data_end,
            resolution="hourly"
        )
        
        # Get all persona files
        persona_files = list(self.prompts_dir.glob("*.txt"))
        if not persona_files:
            raise ValueError("No persona files found in prompts directory!")
        
        # Test results for each persona
        all_results = {}
        
        for persona_file in persona_files:
            self.logger.info(f"Testing persona: {persona_file.name}")
            try:
                # Split data into decision and validation periods
                decision_data = self._slice_market_data(
                    market_data,
                    data_start,
                    self.reference_date
                )
                
                validation_data = self._slice_market_data(
                    market_data,
                    self.reference_date,
                    data_end
                )
                
                results = self._test_single_persona(
                    persona_file,
                    decision_data,
                    validation_data
                )
                all_results[persona_file.stem] = results
                
            except Exception as e:
                self.logger.error(f"Error testing persona {persona_file.name}: {str(e)}")
                continue
        
        # Save consolidated results and get HTML report path
        html_report_path = self._save_consolidated_results(all_results)
        
        # Open the dashboard in the default browser if report was generated
        if html_report_path:
            try:
                abs_path = os.path.abspath(html_report_path)
                url_path = f'file:///{abs_path.replace(os.sep, "/")}'
                self.logger.info(f"Opening dashboard at {url_path}")
                webbrowser.open(url_path)
            except Exception as e:
                self.logger.error(f"Error opening dashboard: {str(e)}")
        
        return all_results

def main():
    import pytz
    
    # Set reference date with timezone (January 14, 2025)
    ny_tz = pytz.timezone('America/New_York')
    reference_date = ny_tz.localize(datetime(2025, 1, 14))
    
    # Configuration
    config = {
        'data_dir': 'market_data',
        'prompts_dir': 'prompts',
        'results_dir': 'backtest_results',
        'lookback_days': 14,  # Historical data for decision
        'forward_days': 7     # Forward testing period
    }
    
    try:
        # Initialize runner with reference date
        runner = TradingSystemRunner(
            data_dir=config['data_dir'],
            prompts_dir=config['prompts_dir'],
            results_dir=config['results_dir'],
            reference_date=reference_date
        )
        
        # Run historical test
        results = runner.run_historical_test(
            lookback_days=config['lookback_days'],
            forward_days=config['forward_days']
        )
        
        print(f"\nHistorical test completed for reference date: {reference_date}")
        print("\nSummary of results:")
        for persona, data in results.items():
            if 'performance_metrics' not in data:
                continue
            metrics = data['performance_metrics']
            print(f"\n{persona}:")
            print(f"Win Rate: {metrics.get('win_rate', 0)}%")
            print(f"Average Return: {metrics.get('avg_return', 0)}%")
            print(f"Max Loss: {metrics.get('max_loss', 0)}%")
            print(f"Max Gain: {metrics.get('max_gain', 0)}%")
            
    except Exception as e:
        logging.error(f"Error running historical test: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()