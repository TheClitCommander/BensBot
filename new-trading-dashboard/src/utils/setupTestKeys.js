// Setup API keys for development using real paper trading accounts
// This should be replaced with proper authentication in production

// This file is imported in index.tsx to set up the API keys on application startup

export function setupTestKeys() {
  // TRADIER PAPER TRADING ACCOUNT
  // Set up Tradier API key in localStorage
  localStorage.setItem('tradier_api_key', 'KU2iUnOZIUFre0wypgyOn8TgmGxI'); 
  localStorage.setItem('tradier_account_number', 'VA1201776');
  localStorage.setItem('tradier_endpoint', 'https://api.tradier.com/v1');
  
  // For testing purposes, set obviously different account balances
  // so we can easily tell if portfolio switching is working
  localStorage.setItem('tradier_mock_balance', '450000');
  
  // Standard format for our config store
  localStorage.setItem('apiKeys', JSON.stringify({
    tradier: {
      key: 'KU2iUnOZIUFre0wypgyOn8TgmGxI',
      accountNumber: 'VA1201776',
      isPaper: true
    }
  }));
  
  localStorage.setItem('alpaca_api_key', 'PKYBHCCT1DIMGZX6P64A');
  localStorage.setItem('alpaca_api_secret', 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO');
  localStorage.setItem('alpaca_endpoint', 'https://paper-api.alpaca.markets');
  
  // We don't have real E*TRADE credentials, so using mock ones
  if (!localStorage.getItem('etrade_key')) {
    localStorage.setItem('etrade_key', 'MOCK_ETRADE_KEY');
  }
  
  if (!localStorage.getItem('etrade_secret')) {
    localStorage.setItem('etrade_secret', 'MOCK_ETRADE_SECRET');
  }
  
  // Set a default selected portfolio if it doesn't exist
  if (!localStorage.getItem('selectedPortfolio')) {
    localStorage.setItem('selectedPortfolio', 'tradier_paper');
  }
  
  // Reset connection status to force fresh API connections
  localStorage.removeItem('tradier_connected');
  localStorage.removeItem('alpaca_connected');
  localStorage.removeItem('etrade_connected');
  
  // Add mock balances for different brokers for fallback if API connections fail
  localStorage.setItem('tradier_mock_balance', '450000');
  localStorage.setItem('alpaca_mock_balance', '275000');
  
  // Standard format for our config store
  const existingKeys = JSON.parse(localStorage.getItem('apiKeys') || '{}');
  localStorage.setItem('apiKeys', JSON.stringify({
    ...existingKeys,
    tradier: {
      key: 'KU2iUnOZIUFre0wypgyOn8TgmGxI',
      accountNumber: 'VA1201776',
      isPaper: true
    },
    alpaca: {
      key: 'PKYBHCCT1DIMGZX6P64A',
      secret: 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO',
      isPaper: true
    }
  }));
  
  // Set both brokers to be connected for testing
  localStorage.setItem('tradier_connected', 'true'); 
  localStorage.setItem('alpaca_connected', 'true');
  
  // Set trading mode to paper (for safety)
  localStorage.setItem('tradingMode', 'paper');
  
  // Store selected portfolio to Alpaca by default
  localStorage.setItem('selectedPortfolio', 'alpaca_paper');
  // Allow live trading access (but default to paper mode for safety)
  localStorage.setItem('allow_live_trading', 'true');
  
  // Default to paper trading mode
  localStorage.setItem('trading_mode', 'paper');
  
  console.log('API keys configured for paper trading accounts...');
  console.log('Paper trading API keys setup complete with test balances');
};

export default setupTestKeys;
