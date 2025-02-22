from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class LLMResponseValidator:
    """Validates JSON responses from LLM trading agents."""
    
    @staticmethod
    def validate_data_request(response: Dict[str, Any], available_tickers: List[str]) -> Dict[str, Any]:
        """
        Validates data request format from LLM.
        
        Args:
            response: Dictionary containing LLM response
            available_tickers: List of valid ticker symbols
            
        Returns:
            Validated and cleaned response dictionary
            
        Raises:
            ValueError: If response format is invalid
        """
        # Required fields
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
            
        required_fields = ['tickers', 'timeframe']
        missing_fields = [f for f in required_fields if f not in response]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        # Validate tickers
        if not isinstance(response['tickers'], list):
            raise ValueError("'tickers' must be a list")
            
        if not 2 <= len(response['tickers']) <= 5:
            raise ValueError("Must select between 2-5 tickers")
            
        invalid_tickers = [t for t in response['tickers'] if t not in available_tickers]
        if invalid_tickers:
            raise ValueError(f"Invalid tickers selected: {invalid_tickers}")
            
        # Validate timeframe
        timeframe = response.get('timeframe', {})
        if not isinstance(timeframe, dict):
            raise ValueError("'timeframe' must be a dictionary")
            
        required_timeframe = ['start', 'end', 'resolution']
        missing_timeframe = [f for f in required_timeframe if f not in timeframe]
        if missing_timeframe:
            raise ValueError(f"Missing timeframe fields: {missing_timeframe}")
            
        # Validate dates
        try:
            start_date = datetime.strptime(timeframe['start'], '%Y-%m-%d')
            end_date = datetime.strptime(timeframe['end'], '%Y-%m-%d')
            if end_date <= start_date:
                raise ValueError("End date must be after start date")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {str(e)}")
            
        if timeframe['resolution'] != 'hourly':
            raise ValueError("Resolution must be 'hourly'")
            
            
        return response

    @staticmethod
    def validate_trading_decision(
        response: Dict[str, Any],
        available_tickers: List[str]
    ) -> Dict[str, Any]:
        """
        Validates trading decision format from LLM.
        
        Args:
            response: Dictionary containing LLM response
            available_tickers: List of valid ticker symbols
            
        Returns:
            Validated and cleaned response dictionary
            
        Raises:
            ValueError: If response format is invalid
        """
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
            
        required_fields = [
            'action', 'ticker', 'amount', 'expected_timeframe',
            'expected_profit_percentage'
        ]
        missing_fields = [f for f in required_fields if f not in response]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        # Validate action
        valid_actions = ['BUY', 'SELL', 'SHORT', 'PUT']
        if response['action'] not in valid_actions:
            raise ValueError(f"Invalid action: {response['action']}")
            
        # Validate ticker
        if response['ticker'] not in available_tickers:
            raise ValueError(f"Invalid ticker: {response['ticker']}")
            
        # Validate numeric fields
        try:
            amount = float(response['amount'])
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            profit = float(response['expected_profit_percentage'])
            if not 0 <= profit <= 100:
                raise ValueError("Expected profit must be between 0-100%")
                
        except ValueError as e:
            raise ValueError(f"Invalid numeric value: {str(e)}")
            
        # Validate timeframe format (e.g., "1d", "5d", etc.)
        if not isinstance(response['expected_timeframe'], str) or \
           not response['expected_timeframe'].endswith(('d', 'w', 'm')):
            raise ValueError("Invalid timeframe format")
            
            
        return response

def load_and_validate_trading_decisions(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads and validates trading decisions from a JSON file.
    
    Args:
        filepath: Path to JSON file containing trading decisions
        
    Returns:
        List of validated trading decision dictionaries
    """
    try:
        with open(filepath, 'r') as f:
            decisions = json.load(f)
            
        if not isinstance(decisions, list):
            raise ValueError("File must contain a list of trading decisions")
            
        # Basic structure validation
        required_fields = ['action', 'ticker', 'amount']
        for decision in decisions:
            missing_fields = [f for f in required_fields if f not in decision]
            if missing_fields:
                raise ValueError(f"Decision missing required fields: {missing_fields}")
                
        return decisions
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in file")
    except Exception as e:
        raise ValueError(f"Error loading decisions: {str(e)}")