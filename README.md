# Trading Dashboard

A comprehensive dashboard for monitoring financial markets, portfolio performance, and trading strategies.

## Features
- Portfolio performance tracking
- Real-time news from multiple financial APIs
- Trading strategy management
- Market predictions and analysis
- API usage monitoring

## Setup and Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Trading
```

2. Install the dependencies:
```bash
# Make the script executable
chmod +x install_dependencies.sh

# Run the installation script
./install_dependencies.sh
```

3. Add your API keys to the `.env` file:
```
FINNHUB_API_KEY=your_key_here
MARKETAUX_API_KEY=your_key_here
NEWSDATA_API_KEY=your_key_here
GNEWS_API_KEY=your_key_here
...
```

## Running the Dashboard

Run the dashboard with:
```bash
./run_streamlit_app.sh
```

If you encounter any "Address already in use" errors, you can specify a different port:
```bash
PYTHONPATH=$(pwd) streamlit run app.py --server.port 8501
```

## Troubleshooting

### Missing Dependencies
If you see "No module named 'X'" errors, install the missing package:
```bash
source venv/bin/activate
pip install X
```

### API Authentication Errors
If you see 401 errors from APIs, check that your API keys in the `.env` file are correct and that you haven't exceeded usage limits.

### Port Already in Use
If you see "Address already in use" errors, try a different port:
```bash
PYTHONPATH=$(pwd) streamlit run app.py --server.port XXXX
```
Replace XXXX with an available port number.