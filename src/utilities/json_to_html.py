import json
from pathlib import Path
import sys
from datetime import datetime
from typing import Dict, List, Any

def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics from trading results."""
    metrics = {
        'total_trades': len(trades),
        'directions': {},
        'tickers': {},
        'avg_pnl': 0,
        'total_pnl': 0
    }
    
    for trade in trades:
        # Count directions
        direction = trade['direction']
        metrics['directions'][direction] = metrics['directions'].get(direction, 0) + 1
        
        # Count tickers
        ticker = trade['ticker']
        metrics['tickers'][ticker] = metrics['tickers'].get(ticker, 0) + 1
        
        # Calculate averages and totals
        if 'pnl' in trade:
            metrics['total_pnl'] += trade['pnl']
            metrics['avg_pnl'] = metrics['total_pnl'] / metrics['total_trades']
    
    return metrics

def create_html_report(json_file: str) -> str:
    """Convert trading results JSON to HTML report."""
    with open(json_file, 'r') as f:
        trades = json.load(f)
    
    metrics = calculate_metrics(trades)
    
    css = """
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .trade { 
            border: 1px solid #ddd; 
            margin: 10px 0; 
            padding: 15px;
            border-radius: 4px;
        }
        .long { background-color: #e8f5e9; }
        .short { background-color: #ffebee; }
        .metrics { 
            background: #f5f5f5; 
            padding: 20px; 
            margin: 20px 0;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.4em;
            font-weight: bold;
            color: #2196F3;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f8f8;
            font-weight: bold;
            color: #666;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2196F3;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        h1 {
            margin: 0;
            font-size: 24px;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
    </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Results Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {css}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Trading Results Report</h1>
                <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>

            <div class="metrics">
                <h2>Summary Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Total Trades</div>
                        <div class="metric-value">{metrics['total_trades']}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Total PnL</div>
                        <div class="metric-value">${metrics['total_pnl']:.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Average PnL per Trade</div>
                        <div class="metric-value">${metrics['avg_pnl']:.2f}</div>
                    </div>
                </div>

                <h2>Direction Breakdown</h2>
                <table>
                    <tr>
                        <th>Direction</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
    """
    
    # Add direction breakdown
    for direction, count in metrics['directions'].items():
        percentage = (count / metrics['total_trades']) * 100
        html += f"""
                    <tr>
                        <td>{direction}</td>
                        <td>{count}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
        """
    
    html += """
                </table>
            </div>

            <h2>Trading Results</h2>
            <table>
                <tr>
                    <th>Direction</th>
                    <th>Ticker</th>
                    <th>Position Size</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>PnL</th>
                    <th>PnL %</th>
                    <th>Agent</th>
                    <th>Exit Reason</th>
                </tr>
    """
    
    # Add individual trades
    for trade in trades:
        direction_class = trade['direction'].lower()
        html += f"""
                <tr class="{direction_class}">
                    <td>{trade['direction']}</td>
                    <td>{trade['ticker']}</td>
                    <td>{trade['position_size']}</td>
                    <td>${trade['entry_price']:.2f}</td>
                    <td>${trade['exit_price']:.2f}</td>
                    <td>${trade['pnl']:.2f}</td>
                    <td>{trade['pnl_pct']:.2f}%</td>
                    <td>{trade['agent']}</td>
                    <td>{trade['exit_reason']}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    </body>
    </html>
    """
    
    return html

def convert_json_to_html(json_path: str, output_dir: str = "reports") -> str:
    """Convert JSON file to HTML report and save it."""
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate HTML
        html_content = create_html_report(json_path)
        
        # Create output filename
        json_filename = Path(json_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"{json_filename}_report_{timestamp}.html"
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Report generated successfully: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise

def main():
    if len(sys.argv) < 2:
        print("Usage: python json_to_html.py <path_to_json_file> [output_directory]")
        sys.exit(1)
        
    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "reports"
    
    try:
        report_path = convert_json_to_html(json_path, output_dir)
        print(f"Open {report_path} in your browser to view the report")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()