import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
from typing import List, Dict
import time

class MarketDataCollector:
    def __init__(self, data_folder: str = "market_data"):
        """Initialize the data collector with a storage folder."""
        self.data_folder = data_folder
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
            
    def get_nasdaq100_tickers(self) -> List[str]:
        """Get a subset of major NASDAQ stocks for testing."""
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "PYPL", "INTC", "CSCO", "CMCSA", "ADBE", "QCOM", "TXN", "TMUS", "ABNB", "BKNG", "AMD", "SBUX", "INTU", "CHTR", "ISRG", "MDLZ", "GILD", "LRCX", "REGN", "ADI", "AMAT", "MRVL", "ASML", "MRNA", "KLAC", "MU", "MNST", "AVGO", "TEAM", "DXCM", "ILMN", "BIIB", "SNPS", "CDNS", "ALGN", "WDAY", "IDXX", "NXPI", "FTNT", "CTSH", "EA", "VRSK", "PAYX", "ROST", "ODFL", "CPRT", "ADSK", "FAST", "DLTR", "CTAS", "ZM", "PANW", "VRTX", "CRWD", "EBAY", "MCHP", "DDOG", "XEL", "ANSS", "SWKS", "SIRI", "MTCH", "OKTA", "DOCU", "ZS", "ULTA", "CDW", "FANG", "ETSY", "TTWO", "WBA", "LCID", "RIVN", "PCAR", "ORLY", "MAR", "COST", "PDD", "JD", "DASH", "COIN", "LULU", "ROKU", "NET", "TTD", "RBLX", "SOFI", "UPST", "PLTR"
        ]
    
    def collect_historical_data(self, lookback_days: int = 14) -> None:
        """Collect hourly data for all stocks for the specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        tickers = self.get_nasdaq100_tickers()
        
        # Create a metadata file with collection timestamp
        metadata = {
            'collection_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'number_of_tickers': len(tickers)
        }
        
        pd.DataFrame([metadata]).to_csv(
            f"{self.data_folder}/metadata.csv", index=False
        )
        
        # Collect data for each ticker
        for ticker in tickers:
            try:
                print(f"Collecting data for {ticker}...")
                stock = yf.Ticker(ticker)
                df = stock.history(
                    start=start_date,
                    end=end_date,
                    interval='1h'
                )
                
                if not df.empty:
                    # Add ticker column and reset index to make datetime a column
                    df['Ticker'] = ticker
                    df.reset_index(inplace=True)
                    
                    # Save to CSV
                    filename = f"{self.data_folder}/{ticker}_hourly.csv"
                    df.to_csv(filename, index=False)
                    
                # Sleep to avoid hitting rate limits
                time.sleep(1)
                
            except Exception as e:
                print(f"Error collecting data for {ticker}: {str(e)}")
                continue

    def load_ticker_data(self, ticker: str) -> pd.DataFrame:
        """Load data for a specific ticker."""
        filename = f"{self.data_folder}/{ticker}_hourly.csv"
        if os.path.exists(filename):
            return pd.read_csv(filename)
        return pd.DataFrame()

    def get_data_for_analysis(self, tickers: List[str], 
                            start_date: str, end_date: str,
                            resolution: str = 'hourly') -> Dict[str, pd.DataFrame]:
        """
        Get data for specified tickers and timeframe.
        Returns a dictionary of DataFrames, one for each ticker.
        """
        data = {}
        for ticker in tickers:
            df = self.load_ticker_data(ticker)
            if not df.empty:
                # Convert datetime column
                df['Datetime'] = pd.to_datetime(df['Datetime'])
                
                # Filter by date range
                mask = (df['Datetime'] >= start_date) & (df['Datetime'] <= end_date)
                df = df[mask]
                
                # Resample if needed
                if resolution == 'daily':
                    df = df.resample('D', on='Datetime').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).reset_index()
                
                data[ticker] = df
                
        return data
    def get_historical_data(self, start_date: datetime, end_date: datetime, resolution: str = 'hourly') -> Dict[str, pd.DataFrame]:
        """Collect historical data for a specific date range, preferring local data."""
        logger = logging.getLogger(__name__)
        logger.info(f"\n{'='*80}\nAttempting to load market data:")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        tickers = self.get_nasdaq100_tickers()
        logger.info(f"Looking for data for {len(tickers)} tickers")
        
        historical_data = {}
        missing_files = []
        empty_data = []
        loaded_files = []
        
        # Check local data first
        for ticker in tickers:
            filename = f"{self.data_folder}/{ticker}_hourly.csv"
            if not os.path.exists(filename):
                missing_files.append(ticker)
                continue
                
            df = pd.read_csv(filename)
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            # Filter by date range
            mask = (df['Datetime'] >= start_date) & (df['Datetime'] <= end_date)
            filtered_df = df[mask]
            
            if filtered_df.empty:
                empty_data.append(ticker)
                continue
                
            historical_data[ticker] = filtered_df
            loaded_files.append(ticker)
    
        # Log detailed summary
        logger.info("\nData Loading Summary:")
        if loaded_files:
            logger.info(f"Successfully loaded data for: {', '.join(loaded_files)}")
        if missing_files:
            logger.warning(f"Missing files for: {', '.join(missing_files)}")
        if empty_data:
            logger.warning(f"No data in date range for: {', '.join(empty_data)}")
            
        if not historical_data:
            logger.error("NO VALID MARKET DATA FOUND!")
            logger.error(f"Data folder: {os.path.abspath(self.data_folder)}")
            
            # Check if directory exists
            if not os.path.exists(self.data_folder):
                logger.error("Data directory does not exist!")
            else:
                # List what files are actually there
                actual_files = os.listdir(self.data_folder)
                logger.info(f"Files found in directory: {actual_files}")
        
        logger.info(f"{'='*80}\n")
        return historical_data

def main():
    # Initialize collector
    collector = MarketDataCollector()
    
    # Collect fresh data
    print("Starting data collection...")
    collector.collect_historical_data()
    print("Data collection complete!")
    
    # Test data loading
    test_ticker = collector.get_nasdaq100_tickers()[0]
    df = collector.load_ticker_data(test_ticker)
    print(f"\nSample data for {test_ticker}:")
    print(df.head())

if __name__ == "__main__":
    main()