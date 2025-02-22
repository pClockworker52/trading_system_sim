import json
import requests
import pandas as pd
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from src.validators.llm_response_validator import LLMResponseValidator
import random

class TradingError(Exception):
    """Custom exception for trading-related errors."""
    pass

class LLMResponseError(TradingError):
    """Exception raised for errors in LLM response parsing."""
    pass

class SophisticatedTrader:
    def __init__(self, persona_file: str, prompts_dir: str = "prompts"):
        """
        Initialize trader with a specific trading persona.
        
        Args:
            persona_file (str): Name of the file containing the persona prompt
            prompts_dir (str): Directory containing the prompt files
        """
        self.available_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "PYPL", "INTC", "CSCO", "CMCSA", "ADBE", "QCOM", "TXN", "TMUS", "ABNB", "BKNG", "AMD", "SBUX", "INTU", "CHTR", "ISRG", "MDLZ", "GILD", "LRCX", "REGN", "ATVI", "ADI", "AMAT", "MRVL", "ASML", "MRNA", "KLAC", "MU", "MNST", "AVGO", "TEAM", "DXCM", "ILMN", "BIIB", "SNPS", "CDNS", "ALGN", "WDAY", "IDXX", "NXPI", "FTNT", "CTSH", "EA", "VRSK", "PAYX", "ROST", "ODFL", "CPRT", "ADSK", "FAST", "DLTR", "CTAS", "ZM", "PANW", "VRTX", "CRWD", "EBAY", "MCHP", "DDOG", "XEL", "ANSS", "SPLK", "SWKS", "SIRI", "MTCH", "OKTA", "DOCU", "SGEN", "ZS", "ULTA", "CDW", "FANG", "ETSY", "TTWO", "WBA", "LCID", "RIVN", "PCAR", "ORLY", "MAR", "COST", "PDD", "JD", "DASH", "COIN", "LULU", "ROKU", "NET", "TTD", "RBLX", "SOFI", "UPST", "PLTR"
        ]
        self.prompts_dir = Path(prompts_dir)
        self.persona_file = persona_file
        self.persona_path = self.prompts_dir / persona_file
        self.persona_name = Path(persona_file).stem
        self.logger = logging.getLogger(__name__)
        self._load_persona()
        self.validator = LLMResponseValidator()
        
    def _load_persona(self):
        """Load the trading persona from file."""
        try:
            with open(self.persona_path, 'r') as f:
                self.base_prompt = f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Persona file {self.persona_file} not found in {self.prompts_dir}")
            
    def _get_base_prompt(self) -> str:
        """Get the complete base prompt including format notes and available tickers."""
        format_notes = """
CRITICAL FORMATTING REQUIREMENTS:
1. Return ONLY the JSON object
2. NO text before or after the JSON
3. NO explanations, NO roleplay, NO additional commentary
4. NO confirmation messages like "I hope this helps" or "Let me know if you need anything else"
5. The response must start with { and end with }
6. The JSON object MUST include only these fields:
   {
     "tickers": ["TICKER1", "TICKER2" ...],   // MUST be of the available tickers
     "timeframe": {
       "start": "YYYY-MM-DD",
       "end": "YYYY-MM-DD",
       "resolution": "hourly"
     }

   }

"""
        return f"{self.base_prompt}\n\nAVAILABLE TICKERS: {', '.join(self.available_tickers)}\n{format_notes}"


    def request_data(self) -> Dict[str, Any]:
        """Request market data to analyze."""
        example_format = """
TASK: Select stocks to analyze based on your persona.
Your response MUST be a valid JSON matching this EXACT format:

REQUIREMENTS:
1. 'tickers' must be an array of 2-5 valid ticker symbols
2. 'timeframe' must be an object with start, end, and resolution fields
3. 'resolution' must be "hourly"
4. Return ONLY the JSON object, NO additional text
"""
        prompt = self._get_base_prompt() + example_format
        response = self._get_llm_response(prompt)
        try:
            validated_response = self.validator.validate_data_request(
                response, 
                self.available_tickers
            )
            return validated_response
        except ValueError as e:
            raise LLMResponseError(f"Invalid response format: {str(e)}")
        # Validate response structure
        if not isinstance(response, dict):
            raise ValueError(f"Invalid response format: {response}")
            
        required_fields = ['tickers', 'timeframe']
        if not all(field in response for field in required_fields):
            raise ValueError(f"Missing required fields in response: {response}")
            
        if not isinstance(response['timeframe'], dict):
            raise ValueError(f"Invalid timeframe format: {response['timeframe']}")
            
        timeframe_fields = ['start', 'end', 'resolution']
        if not all(field in response['timeframe'] for field in timeframe_fields):
            raise ValueError(f"Missing timeframe fields: {response['timeframe']}")
            
        return response
    
    def analyze_and_trade(self, market_data: Dict[str, pd.DataFrame], requested_tickers: list) -> Dict[str, Any]:
        """Analyze provided market data and make trading decisions."""
        data_summary = self._format_market_data(market_data)
        
        example_format = f"""
CRITICAL RESTRICTIONS:
1. You can ONLY trade these tickers: {', '.join(requested_tickers)}
2. Any other tickers will cause the trade to fail
3. Consider ALL available options - don't default to first choices
4. Base decisions on market data analysis, not option ordering
5. Vary your choices based on market conditions

TASK: Make ONE specific trading decision based on the market data.

Market Data Summary:
{data_summary}

Trading Information:
- Entry: All trades enter at the next available closing price
- Exit occurs at whichever comes first:
  1. Profit Target: When daily high/low hits target price
     * LONG: exits at entry_price * (1 + expected_profit_percentage)
     * SHORT: exits at entry_price * (1 - expected_profit_percentage)
  2. Time Limit: At closing price of expected_timeframe if target not hit
- No stop-losses implemented
- Trading fees apply to both entry and exit

RESPONSE FORMAT:
Return ONLY a JSON object with EXACTLY these fields:
{{
    "action": ,         // Must be one of: SHORT, PUT, SELL, BUY  
    "ticker": ,         // Must be one from: {random.sample(requested_tickers, len(requested_tickers))}
    "expected_timeframe": ,  // Must be one of: 5d,2d,13d,1d,3d,...  
    "amount": ,         // Number of shares (10-1000)
    "expected_profit_percentage":    // Expected return (0.01 to 0.20)
}}

CRITICAL:
1. ONLY return the JSON object
2. NO text before or after
3. Start with {{ and end with }}
4. ONLY use tickers from the provided list
"""
        
        try:
            # Get trading decision
            decision = self._get_llm_response(example_format)
            # Add validation:
            try:
                validated_decision = self.validator.validate_trading_decision(
                    decision,
                    requested_tickers
                )
                return validated_decision
            except ValueError as e:
                raise LLMResponseError(f"Invalid trading decision: {str(e)}")
            self.logger.info(f"Raw trading decision: {decision}")
            
            # Validate decision
            required_fields = ['action', 'ticker', 'amount']
            if not all(field in decision for field in required_fields):
                raise ValueError(f"Missing required fields. Got: {list(decision.keys())}")
            
            valid_actions = ['BUY', 'SELL', 'SHORT', 'PUT']
            if decision['action'] not in valid_actions:
                raise ValueError(f"Invalid action: {decision['action']}")
            
            if decision['ticker'] not in requested_tickers:
                raise ValueError(f"Invalid ticker: {decision['ticker']}")
            
            if not isinstance(decision['amount'], (int, float)) or decision['amount'] <= 0:
                raise ValueError(f"Invalid amount: {decision['amount']}")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in analyze_and_trade: {str(e)}")
            raise ValueError(f"Error in analyze_and_trade: {str(e)}")
    
    def _get_llm_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from local Llama2 model and extract valid JSON."""
        url = "http://localhost:11434/api/generate"
        
        data = {
            "model": "llama2",
            "prompt": prompt + "\n\nIMPORTANT: Return ONLY a complete, valid JSON object. NO narrative text, NO roleplay, NO additional text before or after the JSON.",
            "stream": False
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code != 200:
                raise LLMResponseError(f"LLM API error: {response.status_code}")
            
            response_text = response.json()['response'].strip()
            print("\nRaw LLM response:", response_text)
            
            # Find JSON in the response
            try:
                # Remove any text before the first {
                start_idx = response_text.find('{')
                if start_idx == -1:
                    raise LLMResponseError("No JSON object found in response")
                    
                # Remove any text after the last }
                end_idx = response_text.rfind('}')
                if end_idx == -1:
                    raise LLMResponseError("No closing brace found in response")
                    
                # Extract the JSON string
                json_str = response_text[start_idx:end_idx + 1]
                
                # Parse the JSON
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to clean up common issues
                    json_str = json_str.replace('\n', ' ').replace('\r', '')
                    json_str = ' '.join(json_str.split())  # Normalize whitespace
                    result = json.loads(json_str)
                
                # Additional validation for timeframe format
                if 'timeframe' in result:
                    timeframe = result['timeframe']
                    if isinstance(timeframe, dict):
                        if not all(k in timeframe for k in ['start', 'end', 'resolution']):
                            raise LLMResponseError("Missing required timeframe fields")
                
                return result
                
            except json.JSONDecodeError as e:
                raise LLMResponseError(f"Invalid JSON in response: {str(e)}\nProblematic response: {response_text}")
            
        except requests.RequestException as e:
            raise LLMResponseError(f"Failed to connect to LLM API: {str(e)}")
        except Exception as e:
            raise LLMResponseError(f"Unexpected error: {str(e)}")
        
    def _format_market_data(self, market_data: Dict[str, pd.DataFrame]) -> str:
        """Format market data into a simple string for the prompt."""
        summary = []
        for ticker, data in market_data.items():
            if not data.empty:
                latest = data.iloc[-1]
                previous = data.iloc[-2]
                pct_change = ((latest['Close'] / previous['Close']) - 1) * 100
                
                summary.append(f"{ticker} Latest Data:")
                summary.append(f"Close: ${latest['Close']:.2f}")
                summary.append(f"Change: {pct_change:.2f}%")
                summary.append(f"Volume: {latest['Volume']:,.0f}")
                summary.append("---")
        
        return "\n".join(summary)

def save_trading_decisions(decisions: List[Dict[str, Any]]):
    """Save trading decisions to a JSON file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"trading_decisions_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(decisions, indent=2, fp=f)
    
    print(f"\nTrading decisions saved to: {output_file}")

def main():
    # Get all txt files from the prompts directory
    prompts_dir = Path("prompts")
    persona_files = list(prompts_dir.glob("*.txt"))
    
    if not persona_files:
        print("No persona files found in the prompts directory!")
        return
        
    all_decisions = []
    
    # Test each persona
    for persona_file in persona_files:
        print(f"\nTesting trader with persona: {persona_file.name}")
        trader = SophisticatedTrader(persona_file.name)
        
        try:
            # Get data request
            print("Requesting data selection from trader...")
            data_request = trader.request_data()
            print("\nTrader's data request:")
            print(json.dumps(data_request, indent=2))
            
            # Create sample market data for requested tickers
            requested_tickers = data_request["tickers"]
            sample_data = {}
            
            for ticker in requested_tickers:
                sample_data[ticker] = pd.DataFrame({
                    'Close': [100.0 + i for i in range(3)],  # Different values for each ticker
                    'Volume': [1000000 * (i+1) for i in range(3)]
                })
            
            # Get trading decision
            print("\nRequesting trading decision...")
            decision = trader.analyze_and_trade(sample_data, requested_tickers)
            print("\nTrader's decision:")
            print(json.dumps(decision, indent=2))
            
            all_decisions.append(decision)
            
        except Exception as e:
            print(f"Error processing persona {persona_file.name}: {str(e)}")
            continue
    
    # Save all trading decisions
    if all_decisions:
        save_trading_decisions(all_decisions)

if __name__ == "__main__":
    main()