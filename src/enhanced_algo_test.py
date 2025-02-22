from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging

@dataclass
class TradePosition:
    entry_time: datetime
    entry_price: float
    position_size: float
    direction: str  # 'LONG' or 'SHORT'
    ticker: str
    agent_name: str
    reasoning: str

@dataclass
class TradeResult:
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    direction: str
    ticker: str
    fees: float
    pnl: float
    pnl_pct: float
    agent_name: str
    reasoning: str
    exit_reason: str

class BacktestFramework:
    def __init__(
        self,
        transaction_fee_pct: float = 0.001,  # 0.1% per trade
        data_dir: str = "market_data",
        reference_date: datetime = None
    ):
        self.fee_pct = transaction_fee_pct
        self.data_dir = Path(data_dir)
        self.trades: List[TradeResult] = []
        self.current_positions: Dict[str, TradePosition] = {}
        self.reference_date = reference_date
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def prepare_data(
        self,
        start_date: datetime,
        end_date: datetime,
        tickers: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Load and prepare historical data for backtesting.
        Implements strict data validation and cleaning.
        """
        prepared_data = {}
        
        for ticker in tickers:
            file_path = self.data_dir / f"{ticker}_hourly.csv"
            if not file_path.exists():
                self.logger.warning(f"Data file not found for {ticker}")
                continue
                
            try:
                df = pd.read_csv(file_path)
                df['Datetime'] = pd.to_datetime(df['Datetime'])
                
                # Basic data validation
                if df.isnull().any().any():
                    self.logger.warning(f"Found null values in {ticker} data")
                    df = df.fillna(method='ffill')
                
                # Ensure required columns exist
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in df.columns for col in required_cols):
                    self.logger.error(f"Missing required columns in {ticker} data")
                    continue
                
                # Filter date range
                mask = (df['Datetime'] >= start_date) & (df['Datetime'] <= end_date)
                df = df[mask].copy()
                
                if len(df) == 0:
                    self.logger.warning(f"No data in specified range for {ticker}")
                    continue
                
                # Add derived features
                df['Returns'] = df['Close'].pct_change()
                df['Volatility'] = df['Returns'].rolling(24).std()
                
                prepared_data[ticker] = df
                
            except Exception as e:
                self.logger.error(f"Error preparing data for {ticker}: {str(e)}")
                continue
        
        return prepared_data

    def execute_trade(
            self,
            ticker: str,
            action: str,
            market_data: pd.DataFrame,
            position_size: float,
            agent_name: str,
            reasoning: str,
            expected_timeframe: str,
            expected_profit_percentage: float  # New parameter
        ) -> Optional[TradeResult]:
            """
            Execute a trade using historical market data.
            The trade will exit early if the expected_profit_percentage is reached before the expected_timeframe.
            """
            if self.reference_date is None:
                raise ValueError("reference_date must be set to execute trades")
                
            # Parse timeframe
            if not expected_timeframe.endswith('d'):
                raise ValueError(f"Unsupported timeframe format: {expected_timeframe}")
            days = int(expected_timeframe[:-1])
            
            # Calculate entry and max exit times
            entry_time = self.reference_date
            max_exit_time = entry_time + timedelta(days=days)
            
            # Convert Datetime column to datetime if it's not already
            if 'Datetime' in market_data.columns and not pd.api.types.is_datetime64_any_dtype(market_data['Datetime']):
                market_data['Datetime'] = pd.to_datetime(market_data['Datetime'])
            
            # Find entry price and time
            entry_mask = (market_data['Datetime'] >= entry_time)
            if not any(entry_mask):
                raise ValueError(f"No data available at or after entry time {entry_time}")
                
            entry_price = market_data.loc[entry_mask].iloc[0]['Close']
            actual_entry_time = market_data.loc[entry_mask].iloc[0]['Datetime']
            
            # Calculate target price based on position direction
            if action == 'BUY':
                target_price = entry_price * (1 + expected_profit_percentage)
            else:  # SHORT
                target_price = entry_price * (1 - expected_profit_percentage)
            
            # Look for profit target hit or reach max time
            trade_data = market_data[
                (market_data['Datetime'] >= actual_entry_time) & 
                (market_data['Datetime'] <= max_exit_time)
            ]
            
            exit_price = None
            actual_exit_time = None
            
            # Check each day for profit target
            for date, daily_data in trade_data.groupby(trade_data['Datetime'].dt.date):
                if action == 'BUY':
                    if daily_data['High'].max() >= target_price:
                        exit_price = target_price
                        # Find the first time the target was hit
                        actual_exit_time = daily_data.loc[
                            daily_data['High'] >= target_price, 'Datetime'
                        ].iloc[0]
                        break
                else:  # SHORT
                    if daily_data['Low'].min() <= target_price:
                        exit_price = target_price
                        # Find the first time the target was hit
                        actual_exit_time = daily_data.loc[
                            daily_data['Low'] <= target_price, 'Datetime'
                        ].iloc[0]
                        break
            
            # If profit target wasn't hit, use max_exit_time
            if exit_price is None:
                exit_mask = (market_data['Datetime'] >= max_exit_time)
                if not any(exit_mask):
                    raise ValueError(f"No data available at or after exit time {max_exit_time}")
                exit_price = market_data.loc[exit_mask].iloc[0]['Close']
                actual_exit_time = market_data.loc[exit_mask].iloc[0]['Datetime']
            
            # Calculate fees
            entry_value = entry_price * position_size
            exit_value = exit_price * position_size
            entry_fee = entry_value * self.fee_pct
            exit_fee = exit_value * self.fee_pct
            
            # Calculate PnL based on position direction
            if action == 'BUY':
                pnl = (exit_value - entry_value) - (entry_fee + exit_fee)
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            else:  # SHORT
                pnl = (entry_value - exit_value) - (entry_fee + exit_fee)
                pnl_pct = ((entry_price - exit_price) / entry_price) * 100
            
            # Record position
            direction = 'LONG' if action == 'BUY' else 'SHORT'
            position = TradePosition(
                entry_time=actual_entry_time,
                entry_price=entry_price,
                position_size=position_size,
                direction=direction,
                ticker=ticker,
                agent_name=agent_name,
                reasoning=reasoning
            )
            
            self.current_positions[ticker] = position
            
            # Create trade result with appropriate exit reason
            exit_reason = (
                f"Profit target of {expected_profit_percentage*100}% reached" 
                if exit_price == target_price 
                else f"Time-based exit after {expected_timeframe}"
            )
            
            result = TradeResult(
                entry_time=actual_entry_time,
                exit_time=actual_exit_time,
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=position_size,
                direction=direction,
                ticker=ticker,
                fees=entry_fee + exit_fee,
                pnl=pnl,
                pnl_pct=pnl_pct,
                agent_name=agent_name,
                reasoning=reasoning,
                exit_reason=exit_reason
            )
            
            self.trades.append(result)
            return result

    def run_backtest(
            self,
            market_data: Dict[str, pd.DataFrame],
            agent_responses: List[Dict]
        ) -> Tuple[Dict, List[TradeResult]]:
            """Run backtest for trading decisions."""
            self.logger.info("Starting backtest...")
            
            # Reset state
            self.trades = []
            self.current_positions = {}
            
            # Track metrics
            metrics = {
                'total_trades': len(agent_responses),
                'win_rate': 0.0,
                'avg_return': 0.0,
                'max_loss': 0.0,
                'max_gain': 0.0
            }
            
            # Process each agent response
            for response in agent_responses:
                self.logger.info(f"Processing trade: {response}")
                
                if not all(key in response for key in ['ticker', 'action', 'amount', 'expected_timeframe']):
                    self.logger.error(f"Missing required fields in response: {response}")
                    continue
                    
                ticker = response['ticker']
                if ticker not in market_data:
                    self.logger.error(f"No market data for ticker {ticker}")
                    continue
                    
                # Get relevant market data
                df = market_data[ticker]
                if df.empty:
                    self.logger.error(f"Empty market data for ticker {ticker}")
                    continue
                
                try:
                    result = self.execute_trade(
                        ticker=ticker,
                        action=response['action'],
                        market_data=df,
                        position_size=float(response['amount']),
                        agent_name=response.get('persona', 'unknown'),
                        reasoning=response.get('reasoning', ''),
                        expected_timeframe=response['expected_timeframe'],
                        expected_profit_percentage=float(response['expected_profit_percentage'])  # Add this line
                    )
                    
                    if result:
                        self.logger.info(f"Trade result: {result}")
                        
                except Exception as e:
                    self.logger.error(f"Error executing trade: {str(e)}")
                    continue
            
            # Calculate metrics
            if self.trades:
                metrics.update({
                    'win_rate': self._calculate_win_rate(self.trades),
                    'avg_return': self._calculate_avg_return(self.trades),
                    'max_loss': self._calculate_max_loss(self.trades),
                    'max_gain': self._calculate_max_gain(self.trades)
                })
                
            self.logger.info(f"Backtest metrics: {metrics}")
            return metrics, self.trades
    
    def _calculate_win_rate(self, trades: List[TradeResult]) -> float:
        """Calculate win rate for a list of trades."""
        if not trades:
            return 0.0
        winning_trades = len([t for t in trades if t.pnl > 0])
        return round((winning_trades / len(trades)) * 100, 2)
    
    def _calculate_avg_return(self, trades: List[TradeResult]) -> float:
        """Calculate average return percentage."""
        if not trades:
            return 0.0
        returns = [t.pnl_pct for t in trades]
        return round(sum(returns) / len(returns), 2)
    
    def _calculate_max_loss(self, trades: List[TradeResult]) -> float:
        """Calculate maximum loss percentage."""
        if not trades:
            return 0.0
        returns = [t.pnl_pct for t in trades]
        return round(min(returns), 2)
    
    def _calculate_max_gain(self, trades: List[TradeResult]) -> float:
        """Calculate maximum gain percentage."""
        if not trades:
            return 0.0
        returns = [t.pnl_pct for t in trades]
        return round(max(returns), 2)
    
    def _format_trade(self, trade: TradeResult) -> Dict:
        """Format trade result for reporting."""
        return {
            'ticker': trade.ticker,
            'direction': trade.direction,
            'entry_time': trade.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'exit_time': trade.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            'entry_price': round(trade.entry_price, 4),
            'exit_price': round(trade.exit_price, 4),
            'position_size': trade.position_size,
            'pnl': round(trade.pnl, 2),
            'pnl_pct': round(trade.pnl_pct, 2),
            'fees': round(trade.fees, 2),
            'agent': trade.agent_name,
            'reasoning': trade.reasoning,
            'exit_reason': trade.exit_reason
        }

    def generate_report(self, output_dir: Optional[str] = None) -> str:
        """Generate detailed backtest report."""
        metrics = {
            'backtest_summary': {
                'total_trades': len(self.trades),
                'unique_tickers': len(set(t.ticker for t in self.trades)),
                'unique_agents': len(set(t.agent_name for t in self.trades))
            },
            'performance_metrics': {
                'win_rate': self._calculate_win_rate(self.trades),
                'avg_return': self._calculate_avg_return(self.trades),
                'max_loss': self._calculate_max_loss(self.trades),
                'max_gain': self._calculate_max_gain(self.trades)
            },
            'trade_log': [self._format_trade(trade) for trade in self.trades]
        }
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            report_path = output_dir / f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(metrics, indent=2, fp=f)
        
        return json.dumps(metrics, indent=2)
    