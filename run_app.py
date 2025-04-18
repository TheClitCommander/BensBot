from flask import Flask
from ai_backtest_endpoint import add_ai_backtest_endpoint

# Create Flask app
app = Flask(__name__)

# Add the AI backtest endpoint
app = add_ai_backtest_endpoint(app)

# Run the app
if __name__ == "__main__":
    print("Starting Flask server at http://localhost:8000")
    print("API endpoint available at: /api/backtesting/autonomous")
    app.run(debug=True, port=8000) 