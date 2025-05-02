"""
Test script for the AI backtesting endpoint
"""

import requests
import json

# Test data
test_data = {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "timeframes": ["1D", "4H"],
    "strategy_types": ["moving_average_crossover", "rsi_reversal", "breakout_momentum"],
    "market_condition": "Automatic",
    "sectors": ["Tech"]
}

# Send request to the endpoint
try:
    response = requests.post(
        "http://127.0.0.1:5000/api/backtesting/autonomous",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    # Print response
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Success:", result['success'])
        
        # Print summary of results
        if 'results' in result:
            results = result['results']
            print(f"\nExecution ID: {results.get('execution_id')}")
            print(f"Execution time: {results.get('execution_time_seconds')} seconds")
            
            # Print winning strategies
            print("\nTop strategies:")
            for i, strategy in enumerate(results.get('winning_strategies', [])[:3]):
                print(f"  {i+1}. {strategy['strategy']['name']}")
                print(f"     Return: {strategy['aggregate_performance']['return']}%")
                print(f"     Sharpe: {strategy['aggregate_performance']['sharpe_ratio']}")
                print(f"     Win Rate: {strategy['aggregate_performance']['win_rate']}%")
            
            # Print insights
            print("\nInsights:")
            for insight in results.get('ml_insights', {}).get('winning_patterns', []):
                print(f"  - {insight}")
    else:
        print("Error:", response.text)
except Exception as e:
    print(f"Error making request: {e}") 