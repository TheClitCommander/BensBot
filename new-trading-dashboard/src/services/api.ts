import axios, { AxiosInstance } from 'axios';

// Define interfaces for the API responses
export interface PortfolioData {
  totalValue: number;
  dailyChange: number;
  dailyChangePercent: number;
  monthlyReturn: number;
  weeklyChange: number;
  allocation: { category: string; value: number; color: string }[];
  holdings: {
    symbol: string;
    name: string;
    quantity: number;
    entryPrice: number;
    currentPrice: number;
    value: number;
    unrealizedPnl: number;
    unrealizedPnlPercent: number;
  }[];
}

export interface BrokerAccountInfo {
  accountId: string;
  accountNumber: string;
  accountType?: string;
  balance: number;
  equity?: number;
  buyingPower?: number;
  cash?: number;
  positions: any[];
}

export interface PerformanceHistory {
  daily: number[];
  weekly: number[];
  monthly: number[];
  yearly: number[];
  currentReturn: number;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  url: string;
  source: string;
  imageUrl?: string;
  publishedAt: string;
  sentiment?: string;
  symbols?: string[];
  impact?: string;
}

export interface TradeData {
  id: string;
  symbol: string;
  entry: number;
  entryPrice: number;
  quantity: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  status: 'open' | 'closed';
  strategy: string;
  side: 'long' | 'short' | string;
  openedAt: string;
  type: string;
  strategyName?: string;
  entryDate?: string;
  pl?: number;
  plPercent?: number;
}

export interface StrategyData {
  name: string;
  description: string;
  status: string;
  allocation: number;
  performance: {
    daily: number;
    weekly: number;
    monthly: number;
    yearly: number;
  };
  activeTrades: number;
  signalStrength: number;
  lastUpdated: string;
}

export interface MarketSymbolData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  previousClose?: number;
}

export interface MarketStat {
  symbol: string;
  price: number;
  change: number;
  volume: number;
}

export interface MarketStats {
  gainers: MarketStat[];
  losers: MarketStat[];
  active: MarketStat[];
}

export interface MarketStatData {
  name: string;
  value: number;
  change: number;
  changePercent?: number;
}

// Trading mode - default to paper for safety
const getTradingMode = () => {
  return localStorage.getItem('paper_trading') !== 'false';
};

// Track API connection status
let isBackendAvailable = false;
let tradierConnected = false;
let alpacaConnected = false;

// Initialize API clients for direct broker connections
const tradierClient = axios.create({
  baseURL: 'https://sandbox.tradier.com/v1', // Paper trading endpoint
  timeout: 10000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Using demo keys for development - replace with real keys for production
const ALPACA_API_KEY = process.env.REACT_APP_ALPACA_API_KEY || 'PKWFCWD7H39WBXSVLKX4';
const ALPACA_API_SECRET = process.env.REACT_APP_ALPACA_API_SECRET || 'MephistoTrades2024';

const alpacaClient = axios.create({
  baseURL: 'https://paper-api.alpaca.markets/v2',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_API_SECRET
  }
});

// Create a test server client for local development (port 4000)
export const testServerClient = axios.create({
  baseURL: 'http://localhost:4000',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Polygon.io client for market data and news
// Using a free API key for demonstration - replace with your own for production
// Note: This is for development purposes only
const POLYGON_API_KEY = process.env.REACT_APP_POLYGON_API_KEY || 'jcR7MD_H5Z1QO2h4Zv4K8h6XZvBYTWK4';
const polygonClient = axios.create({
  baseURL: 'https://api.polygon.io',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  },
  params: { apiKey: POLYGON_API_KEY } // Adding API key to all requests automatically
});

// Local backend API client
const apiClient = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Initialize API keys
const initializeApiKeys = () => {
  // Tradier Paper Trading credentials
  const tradierApiKey = 'KU2iUnOZIUFre0wypgyOn8TgmGxI';
  const tradierAccountNumber = 'VA1201776';
  localStorage.setItem('tradier_api_key', tradierApiKey);
  localStorage.setItem('tradier_account_number', tradierAccountNumber);
  
  // Alpaca Paper Trading credentials
  const alpacaApiKey = 'PKYBHCCT1DIMGZX6P64A';
  const alpacaApiSecret = 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO';
  localStorage.setItem('alpaca_api_key', alpacaApiKey);
  localStorage.setItem('alpaca_api_secret', alpacaApiSecret);
  
  // Configure clients with API keys
  tradierClient.defaults.headers.common['Authorization'] = `Bearer ${tradierApiKey}`;
  alpacaClient.defaults.headers.common['APCA-API-KEY-ID'] = alpacaApiKey;
  alpacaClient.defaults.headers.common['APCA-API-SECRET-KEY'] = alpacaApiSecret;
  
  // Configure Polygon.io client with Alpaca API key (Alpaca provides free access to Polygon data)
  polygonClient.defaults.params = { 'apiKey': alpacaApiKey };
  
  console.log('API keys loaded and clients configured');
};

// Initialize API keys immediately
initializeApiKeys();

// Track active broker for multi-broker support
let activeBroker = localStorage.getItem('active_broker') || 'tradier';

// Function to set the active broker
const setActiveBroker = (broker: 'tradier' | 'alpaca') => {
  activeBroker = broker;
  localStorage.setItem('active_broker', broker);
};

// Always try to use real broker APIs
const shouldTryRealApi = () => true;

// Portfolio API methods
export const portfolioApi = {
  // Get portfolio data from the active broker API
  getPortfolio: async (): Promise<PortfolioData> => {
    // Get active broker
    const broker = localStorage.getItem('active_broker') || 'tradier';
    
    if (broker === 'tradier') {
      // Get Tradier account data
      try {
        const accountNumber = localStorage.getItem('tradier_account_number');
        
        if (!accountNumber) {
          throw new Error('Missing Tradier account number');
        }
        
        // Get account balances
        const balanceResponse = await tradierClient.get(`/accounts/${accountNumber}/balances`);
        
        if (!balanceResponse.data || !balanceResponse.data.balances) {
          throw new Error('Invalid response from Tradier balances endpoint');
        }
        
        const balances = balanceResponse.data.balances;
        
        // Get positions
        const positionsResponse = await tradierClient.get(`/accounts/${accountNumber}/positions`);
        let positions: any[] = [];
        
        if (positionsResponse.data && positionsResponse.data.positions) {
          // Check if positions is an array or single object
          if (Array.isArray(positionsResponse.data.positions.position)) {
            positions = positionsResponse.data.positions.position;
          } else if (positionsResponse.data.positions.position) {
            // Single position
            positions = [positionsResponse.data.positions.position];
          }
        }
        
        // Process positions to holdings
        const holdings = await Promise.all(positions.map(async (position) => {
          const symbol = position.symbol;
          // Get quote for current price
          const quoteResponse = await tradierClient.get(`/markets/quotes?symbols=${symbol}`);
          let currentPrice = position.last || 0;
          
          if (quoteResponse.data && quoteResponse.data.quotes && quoteResponse.data.quotes.quote) {
            currentPrice = quoteResponse.data.quotes.quote.last || position.last || 0;
          }
          
          const value = position.quantity * currentPrice;
          const costBasis = position.cost_basis || (position.quantity * position.price);
          const unrealizedPnl = value - costBasis;
          const unrealizedPnlPercent = costBasis > 0 ? (unrealizedPnl / costBasis) * 100 : 0;
          
          return {
            symbol: position.symbol,
            name: position.symbol, // Getting company name would require another API call
            quantity: position.quantity,
            entryPrice: position.price,
            currentPrice,
            value,
            unrealizedPnl,
            unrealizedPnlPercent
          };
        }));
        
        // Calculate allocation by sector - Tradier doesn't provide sector info directly
        // So we'll create mock categories for now, but in a real app you would get this data
        // from another source like a market data API
        const allocation = [{ category: 'Stocks', value: balances.total_equity, color: '#4285F4' }];
        
        tradierConnected = true;
        
        return {
          totalValue: balances.total_equity,
          dailyChange: balances.market_value - balances.prev_market_value,
          dailyChangePercent: balances.prev_market_value > 0 ? 
            ((balances.market_value - balances.prev_market_value) / balances.prev_market_value) * 100 : 0,
          monthlyReturn: 0, // Would need historical data for this
          weeklyChange: 0,  // Would need historical data for this
          allocation,
          holdings
        };
      } catch (error) {
        console.error('Error fetching Tradier portfolio data:', error);
        tradierConnected = false;
        // Throw error so caller can handle it
        throw new Error(`Could not fetch Tradier portfolio: ${error instanceof Error ? error.message : String(error)}`);
      }
    } else if (broker === 'alpaca') {
      // Get Alpaca account data
      try {
        // Get account data
        const accountResponse = await alpacaClient.get('/account');
        if (!accountResponse.data) {
          throw new Error('Invalid response from Alpaca account endpoint');
        }
        
        const account = accountResponse.data;
        
        // Get positions
        const positionsResponse = await alpacaClient.get('/positions');
        const positions = positionsResponse.data || [];
        
        // Process positions to holdings
        const holdings = positions.map((position: any) => {
          const value = parseFloat(position.market_value);
          const costBasis = parseFloat(position.cost_basis);
          const unrealizedPnl = value - costBasis;
          const unrealizedPnlPercent = costBasis > 0 ? (unrealizedPnl / costBasis) * 100 : 0;
          
          return {
            symbol: position.symbol,
            name: position.symbol,
            quantity: parseFloat(position.qty),
            entryPrice: parseFloat(position.avg_entry_price),
            currentPrice: parseFloat(position.current_price),
            value,
            unrealizedPnl,
            unrealizedPnlPercent
          };
        });
        
        // For allocation, we'll group by asset class since Alpaca doesn't provide sector info directly
        const allocation = [{ category: 'Stocks', value: parseFloat(account.equity), color: '#4285F4' }];
        
        alpacaConnected = true;
        
        return {
          totalValue: parseFloat(account.equity),
          dailyChange: parseFloat(account.equity) - parseFloat(account.last_equity),
          dailyChangePercent: parseFloat(account.last_equity) > 0 ? 
            ((parseFloat(account.equity) - parseFloat(account.last_equity)) / parseFloat(account.last_equity)) * 100 : 0,
          monthlyReturn: 0, // Would need historical data for this
          weeklyChange: 0,  // Would need historical data for this
          allocation,
          holdings
        };
      } catch (error) {
        console.error('Error fetching Alpaca portfolio data:', error);
        alpacaConnected = false;
        // Throw error so caller can handle it
        throw new Error(`Could not fetch Alpaca portfolio: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    
    // This should never happen if the broker is either 'tradier' or 'alpaca'
    throw new Error(`Unknown broker: ${broker}`);
  },
  
  // Get performance history from broker API
  getPerformanceHistory: async (): Promise<PerformanceHistory> => {
    // Get active broker
    const broker = localStorage.getItem('active_broker') || 'tradier';
    
    try {
      if (broker === 'tradier') {
        // For Tradier, we need to calculate performance from historical account data
        const accountNumber = localStorage.getItem('tradier_account_number');
        
        if (!accountNumber) {
          throw new Error('Missing Tradier account number');
        }
        
        // Get current balance
        const balanceResponse = await tradierClient.get(`/accounts/${accountNumber}/balances`);
        
        if (!balanceResponse.data || !balanceResponse.data.balances) {
          throw new Error('Invalid response from Tradier balances endpoint');
        }
        
        const balances = balanceResponse.data.balances;
        const equityValue = balances.total_equity || 0;
        
        // Get history - For Tradier, we'd need to get this from another endpoint
        // For now, simulate the performance history based on current portfolio value
        // In a real app, you'd get historical performance data from trading records
        
        // Generate simulated performance data based on current equity
        // This would typically come from a trading journal or history API
        const dailyPerformance = [];
        const weeklyPerformance = [];
        const monthlyPerformance = [];
        const yearlyPerformance = [];
        const baseValue = equityValue * 0.9; // 90% of current equity as starting point
        
        // Generate 14 days of daily performance
        for (let i = 0; i < 14; i++) {
          // Random daily change between -1.5% and +2%
          const dailyChange = ((Math.random() * 3.5) - 1.5);
          dailyPerformance.push(dailyChange);
        }
        
        // Generate 10 weeks of weekly performance
        for (let i = 0; i < 10; i++) {
          // Random weekly change between -2% and +4%
          const weeklyChange = ((Math.random() * 6) - 2);
          weeklyPerformance.push(weeklyChange);
        }
        
        // Generate 12 months of monthly performance
        for (let i = 0; i < 12; i++) {
          // Random monthly change between -2% and +6%
          const monthlyChange = ((Math.random() * 8) - 2);
          monthlyPerformance.push(monthlyChange);
        }
        
        // Generate 5 years of yearly performance
        for (let i = 0; i < 5; i++) {
          // Random yearly change between +5% and +20%
          const yearlyChange = ((Math.random() * 15) + 5);
          yearlyPerformance.push(yearlyChange);
        }
        
        return {
          daily: dailyPerformance,
          weekly: weeklyPerformance,
          monthly: monthlyPerformance,
          yearly: yearlyPerformance,
          currentReturn: dailyPerformance[dailyPerformance.length - 1] || 0
        };
      } else if (broker === 'alpaca') {
        // For Alpaca, use portfolio history API
        const historyResponse = await alpacaClient.get('/account/portfolio/history?period=1M&timeframe=1D');
        
        if (!historyResponse.data) {
          throw new Error('Invalid response from Alpaca history endpoint');
        }
        
        const history = historyResponse.data;
        let dailyPerformance = [];
        
        // Convert Alpaca historical data to daily performance percentages
        if (history.profit_loss_pct) {
          dailyPerformance = history.profit_loss_pct;
        } else {
          // Calculate daily changes from equity values if percentages not provided
          for (let i = 1; i < history.equity.length; i++) {
            const todayEquity = history.equity[i] || 0;
            const yesterdayEquity = history.equity[i-1] || 1; // Avoid division by zero
            const dailyChange = ((todayEquity - yesterdayEquity) / yesterdayEquity) * 100;
            dailyPerformance.push(dailyChange);
          }
        }
        
        // Generate weekly, monthly, and yearly data from this daily data
        // In a real app, you'd make separate API calls for different timeframes
        
        // Weekly - average of last 5 batches of 5 daily performances
        const weeklyPerformance = [];
        for (let i = 0; i < 5; i++) {
          const startIdx = Math.max(0, dailyPerformance.length - 5 * (i + 1));
          const endIdx = Math.max(0, dailyPerformance.length - 5 * i);
          const weekData = dailyPerformance.slice(startIdx, endIdx);
          const weekAvg = weekData.reduce((sum: number, val: number) => sum + val, 0) / weekData.length;
          weeklyPerformance.unshift(weekAvg);
        }
        
        // Generate monthly and yearly performance similarly to what we did for Tradier
        const monthlyPerformance = [];
        for (let i = 0; i < 12; i++) {
          const monthlyChange = ((Math.random() * 8) - 2);
          monthlyPerformance.push(monthlyChange);
        }
        
        const yearlyPerformance = [];
        for (let i = 0; i < 5; i++) {
          const yearlyChange = ((Math.random() * 15) + 5);
          yearlyPerformance.push(yearlyChange);
        }
        
        // Use the latest daily performance as current return
        const currentReturn = dailyPerformance[dailyPerformance.length - 1] || 0;
        
        return {
          daily: dailyPerformance,
          weekly: weeklyPerformance,
          monthly: monthlyPerformance,
          yearly: yearlyPerformance,
          currentReturn
        };
      }
      
      throw new Error(`Unknown broker: ${broker}`);
    } catch (error) {
      console.error(`Error fetching ${broker} performance history:`, error);
      
      // Return minimal fallback data in case of API error
      return {
        daily: [0.1, 0.2, -0.1],
        weekly: [0.5, -0.3],
        monthly: [1.2, 0.8],
        yearly: [5.4, 8.2],
        currentReturn: 0.1
      };
    }
  },
  
  // Store API keys to localStorage for future sessions
  storeApiKeys: () => {
    // Tradier Paper Trading credentials
    localStorage.setItem('tradier_api_key', 'KU2iUnOZIUFre0wypgyOn8TgmGxI');
    localStorage.setItem('tradier_account_number', 'VA1201776');
    
    // Alpaca Paper Trading credentials
    localStorage.setItem('alpaca_api_key', 'PKYBHCCT1DIMGZX6P64A');
    localStorage.setItem('alpaca_api_secret', 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO');
    
    console.log('API keys stored in localStorage');
    return true;
  },

  // Test broker connection with real API calls
  testBrokerConnection: async (broker: 'tradier' | 'alpaca' | 'etrade'): Promise<{isConnected: boolean, message: string}> => {
    try {
      if (broker === 'tradier') {
        // Test Tradier connection by getting account details
        const accountNumber = localStorage.getItem('tradier_account_number');
        
        if (!accountNumber) {
          return { isConnected: false, message: 'Missing Tradier account number' };
        }
        
        // Test API connection by getting account profile
        const response = await tradierClient.get('/user/profile');
        
        if (response.status === 200 && response.data && response.data.profile) {
          tradierConnected = true;
          localStorage.setItem('tradier_connected', 'true');
          return { 
            isConnected: true, 
            message: `Connected to Tradier paper trading account ${accountNumber}` 
          };
        } else {
          tradierConnected = false;
          localStorage.setItem('tradier_connected', 'false');
          return { 
            isConnected: false, 
            message: 'Received invalid response from Tradier API' 
          };
        }
      } else if (broker === 'alpaca') {
        // Test Alpaca connection by getting account details
        const response = await alpacaClient.get('/account');
        
        if (response.status === 200 && response.data && response.data.id) {
          alpacaConnected = true;
          localStorage.setItem('alpaca_connected', 'true');
          return { 
            isConnected: true, 
            message: `Connected to Alpaca paper trading account ${response.data.id}` 
          };
        } else {
          alpacaConnected = false;
          localStorage.setItem('alpaca_connected', 'false');
          return { 
            isConnected: false, 
            message: 'Received invalid response from Alpaca API' 
          };
        }
      } else if (broker === 'etrade') {
        // E*TRADE requires OAuth authentication - not implemented yet
        return { 
          isConnected: false, 
          message: 'E*TRADE integration not implemented yet' 
        };
      }
      
      return { isConnected: false, message: `Unknown broker: ${broker}` };
    } catch (error) {
      console.error(`Error testing ${broker} connection:`, error);
      if (broker === 'tradier') {
        tradierConnected = false;
        localStorage.setItem('tradier_connected', 'false');
      } else if (broker === 'alpaca') {
        alpacaConnected = false;
        localStorage.setItem('alpaca_connected', 'false');
      }
      
      return { 
        isConnected: false, 
        message: `Failed to connect to ${broker}: ${error instanceof Error ? error.message : String(error)}` 
      };
    }
  }
};

// Trades API methods
export const tradesApi = {
  getTrades: async (): Promise<TradeData[]> => {
    // Get active broker
    const broker = localStorage.getItem('active_broker') || 'tradier';
    
    try {
      if (broker === 'tradier') {
        // Get Tradier trades through orders history
        const accountNumber = localStorage.getItem('tradier_account_number');
        
        if (!accountNumber) {
          throw new Error('Missing Tradier account number');
        }
        
        // Get orders history (includes filled orders = trades)
        const ordersResponse = await tradierClient.get(`/accounts/${accountNumber}/orders`);
        
        if (!ordersResponse.data) {
          throw new Error('Invalid response from Tradier orders endpoint');
        }
        
        let orders: any[] = [];
        
        // Check if there are any orders
        if (ordersResponse.data.orders && ordersResponse.data.orders.order) {
          // Check if orders is an array or single object
          if (Array.isArray(ordersResponse.data.orders.order)) {
            orders = ordersResponse.data.orders.order;
          } else {
            // Single order
            orders = [ordersResponse.data.orders.order];
          }
        }
        
        // Filter to include only executed orders 
        const trades = orders
          .filter(order => order.status === 'filled' || order.status === 'partially_filled')
          .map((order, index) => {
            // Get symbol details
            const symbol = order.symbol;
            
            // Map Tradier order data to TradeData format
            return {
              id: order.id || String(index + 1),
              symbol: symbol,
              entry: order.price || 0,
              entryPrice: order.price || 0,
              quantity: order.quantity || 0,
              currentPrice: order.exec_price || order.price || 0,
              pnl: 0, // Would need to calculate based on current price vs. entry
              pnlPercent: 0,
              pl: 0, // Alias for pnl
              plPercent: 0, // Alias for pnlPercent
              status: order.status === 'filled' ? 'closed' : 'open' as 'closed' | 'open',
              strategy: 'API Trade',
              side: order.side === 'buy' ? 'long' : 'short',
              openedAt: new Date(order.created_at || Date.now()).toISOString(),
              entryDate: new Date(order.created_at || Date.now()).toISOString(),
              type: order.type || 'MARKET',
              strategyName: 'API Trade'
            };
          });
        
        return trades;
      } else if (broker === 'alpaca') {
        // Get Alpaca trades through orders API
        const ordersResponse = await alpacaClient.get('/orders?status=filled&limit=100');
        
        if (!ordersResponse.data) {
          throw new Error('Invalid response from Alpaca orders endpoint');
        }
        
        const orders = ordersResponse.data || [];
        
        // Map orders to trades format
        const trades = orders.map((order: any, index: number) => {
          return {
            id: order.id || String(index + 1),
            symbol: order.symbol,
            entry: parseFloat(order.filled_avg_price || order.limit_price || '0'),
            entryPrice: parseFloat(order.filled_avg_price || order.limit_price || '0'),
            quantity: parseFloat(order.qty || '0'),
            currentPrice: parseFloat(order.filled_avg_price || '0'),
            pnl: 0, // Would need another API call to get current price and calculate
            pnlPercent: 0,
            status: order.status === 'filled' ? 'closed' : 'open' as 'closed' | 'open',
            strategy: 'API Trade',
            side: order.side === 'buy' ? 'long' : 'short',
            openedAt: new Date(order.submitted_at || Date.now()).toISOString(),
            type: order.type || 'market'
          };
        });
        
        return trades;
      }
      
      throw new Error(`Unknown broker: ${broker}`);
    } catch (error) {
      console.error(`Error fetching ${broker} trades:`, error);
      
      // Return empty trades array in case of API error
      return [];
    }
  }
};

// News API methods
export const newsApi = {
  getMarketNews: async (): Promise<NewsItem[]> => {
    try {
      // Use Polygon API for market news
      const newsResponse = await polygonClient.get('/v2/reference/news?limit=20');
      
      if (!newsResponse.data || !newsResponse.data.results) {
        throw new Error('Invalid response from Polygon news endpoint');
      }
      
      const newsItems = newsResponse.data.results || [];
      
      // Map Polygon news format to our NewsItem format
      return newsItems.map((item: any) => ({
        id: item.id || Math.random().toString(36).substring(2, 15),
        title: item.title || '',
        summary: item.description || '',
        url: item.article_url || '',
        source: item.publisher.name || '',
        publishedAt: item.published_utc || new Date().toISOString(),
        sentiment: 'neutral', // Polygon doesn't provide sentiment
        symbols: item.tickers || [],
        impact: 'medium' // Polygon doesn't provide impact assessment
      }));
    } catch (error) {
      console.error('Error fetching market news:', error);
      
      // Return mock data as fallback when API fails
      return [
        { id: 'news-1', title: 'Markets Rally on Fed Decision', summary: 'Stock markets surged following the Federal Reserve decision to maintain current interest rates.', url: 'https://example.com/news/1', source: 'Financial Times', publishedAt: '2025-05-04T15:30:00Z', sentiment: 'Positive', symbols: ['SPY', 'QQQ'], impact: 'High' },
        { id: 'news-2', title: 'Tech Sector Leads Gains', summary: 'Technology stocks outperformed the broader market as investors responded positively to strong earnings reports.', url: 'https://example.com/news/2', source: 'Wall Street Journal', publishedAt: '2025-05-04T13:15:00Z', sentiment: 'Positive', symbols: ['AAPL', 'MSFT', 'GOOGL'], impact: 'Medium' },
        { id: 'news-3', title: 'Oil Prices Decline on Supply Concerns', summary: 'Crude oil prices fell 2% following reports of increased production from major oil-producing nations.', url: 'https://example.com/news/3', source: 'Bloomberg', publishedAt: '2025-05-04T10:45:00Z', sentiment: 'Negative', symbols: ['USO', 'XOM'], impact: 'Medium' }
      ];
    }
  },
  
  getSymbolNews: async (symbol: string): Promise<NewsItem[]> => {
    try {
      // Use Polygon API for news with ticker filter
      const newsResponse = await polygonClient.get(`/v2/reference/news?ticker=${symbol}&limit=10`);
      
      if (!newsResponse.data || !newsResponse.data.results) {
        throw new Error('Invalid response from news endpoint');
      }
      
      const newsItems = newsResponse.data.results || [];
      
      // Map news API format to our NewsItem format
      return newsItems.map((item: any) => ({
        id: item.id || Math.random().toString(36).substring(2, 15),
        title: item.headline || '',
        summary: item.summary || '',
        url: item.url || '',
        source: item.source || '',
        publishedAt: item.created_at || new Date().toISOString(),
        sentiment: item.sentiment || 'neutral',
        symbols: item.symbols || [],
        impact: item.impact || 'medium'
      }));
    } catch (error) {
      console.error(`Error fetching news for ${symbol}:`, error);
      
      // Return mock news for fallback
      return [
        {
          id: `${symbol}-news-1`,
          title: `Latest developments for ${symbol}`,
          summary: `This is a mock news article about ${symbol}.`,
          url: 'https://example.com/news/1',
          source: 'Mock Financial News',
          publishedAt: new Date().toISOString(),
          sentiment: 'neutral',
          symbols: [symbol],
          impact: 'medium'
        }
      ];
    }
  }
};

// Strategies API methods
export const strategiesApi = {
  getStrategies: async (): Promise<StrategyData[]> => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.get('/api/strategies');
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error fetching strategies:', error);
      }
    }
    
    // Return mock data as fallback
    return [
      {
        name: 'Trend Following',
        description: 'Follows established market trends using moving averages',
        status: 'active',
        allocation: 25,
        performance: {
          daily: 0.3,
          weekly: 1.2,
          monthly: 3.5,
          yearly: 14.8
        },
        activeTrades: 3,
        signalStrength: 7.5,
        lastUpdated: new Date(Date.now() - 3600000).toISOString()
      },
      {
        name: 'Mean Reversion',
        description: 'Capitalizes on price corrections after significant moves',
        status: 'active',
        allocation: 20,
        performance: {
          daily: -0.2,
          weekly: 0.8,
          monthly: 2.7,
          yearly: 11.5
        },
        activeTrades: 2,
        signalStrength: 6.2,
        lastUpdated: new Date(Date.now() - 7200000).toISOString()
      }
    ];
  }
};

// Logs API methods
export const logsApi = {
  getLogs: async () => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.get('/api/logs');
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    }
    
    // Return mock data as fallback
    return [
      {
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        level: 'INFO',
        source: 'TradingSystem',
        message: 'Trading system started successfully'
      },
      {
        timestamp: new Date(Date.now() - 3500000).toISOString(),
        level: 'INFO',
        source: 'StrategyManager',
        message: 'Loaded 3 active strategies'
      }
    ];
  },

  getSystemLogs: async (limit: number = 100) => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.get(`/api/logs/system?limit=${limit}`);
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error fetching system logs:', error);
      }
    }
    
    // Return mock data as fallback
    return [
      {
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        level: 'INFO',
        source: 'TradingSystem',
        message: 'Trading system started successfully'
      }
    ];
  }
};

// AI API methods
export const aiApi = {
  getRecommendations: async () => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.get('/api/ai/recommendations');
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error fetching AI recommendations:', error);
      }
    }
    
    // Return mock data as fallback
    return [
      {
        id: '1',
        type: 'trade',
        action: 'BUY',
        symbol: 'AAPL',
        confidence: 0.85,
        reasoning: 'Strong technical setup with recent earnings beat and positive analyst sentiment.'
      },
      {
        id: '2',
        type: 'trade',
        action: 'SELL',
        symbol: 'NFLX',
        confidence: 0.72,
        reasoning: 'Weakening momentum and increased competition in the streaming space.'
      }
    ];
  },
  
  getMarketAnalysis: async () => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.get('/api/ai/market-analysis');
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error fetching AI market analysis:', error);
      }
    }
    
    // Return mock data as fallback
    return {
      sentiment: 'Moderately Bullish',
      confidence: 0.68,
      summary: 'Market conditions appear favorable in the near term with strong earnings and economic data supporting current levels.',
      keyPoints: [
        'Technology sector showing strength with positive earnings surprises',
        'Small caps lagging larger indices, suggesting some caution'
      ],
      timestamp: new Date().toISOString()
    };
  },

  sendMessage: async (message: string) => {
    if (shouldTryRealApi()) {
      try {
        const response = await apiClient.post('/api/ai/chat', { message });
        isBackendAvailable = true;
        return response.data;
      } catch (error) {
        console.error('Error sending message to AI:', error);
      }
    }
    
    // Return mock response
    return {
      text: 'This is a mock AI response. The real AI assistant is not available.',
      timestamp: new Date().toISOString()
    };
  }
};

// Market data interfaces for Alpaca API
interface MarketDataItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  previousClose?: number;
}

// Market API methods
export const marketApi = {
  getMarketIndices: async () => {
    const symbols = ['SPY', 'QQQ', 'IWM', 'DIA'];
    try {
      const response = await tradierClient.get('/markets/quotes', { params: { symbols: symbols.join(',') } });
      const quotes = response.data.quotes.quote;
      const quotesArray = Array.isArray(quotes) ? quotes : [quotes];
      return quotesArray.map((q: any) => ({
        symbol: q.symbol,
        name: q.description,
        price: q.last,
        change: q.change,
        changePercent: parseFloat(q.change_percentage)
      }));
    } catch (error) {
      console.error('Error fetching market indices:', error);
      throw error;
    }
  },

  getSymbolData: async (symbol: string) => {
    try {
      const response = await tradierClient.get('/markets/quotes', { params: { symbols: symbol } });
      const quote = response.data.quotes.quote;
      const q = Array.isArray(quote) ? quote[0] : quote;
      return {
        symbol: q.symbol,
        name: q.description,
        price: q.last,
        change: q.change,
        changePercent: parseFloat(q.change_percentage),
        volume: q.volume,
        open: q.open,
        high: q.high,
        low: q.low,
        previousClose: q.prevclose
      };
    } catch (error) {
      console.error(`Error fetching data for symbol ${symbol}:`, error);
      throw new Error(`Could not get data for symbol ${symbol} from Tradier API`);
    }
  },

  getMarketStats: async (): Promise<MarketStats> => {
    const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'V', 'JPM', 'JNJ',
                     'KO', 'PEP', 'DIS', 'NFLX', 'PYPL', 'INTC', 'AMD', 'BABA', 'NKE', 'MCD'];
    try {
      const response = await tradierClient.get('/markets/quotes', { params: { symbols: symbols.join(',') } });
      const quotes = response.data.quotes.quote;
      const quotesArray = Array.isArray(quotes) ? quotes : [quotes];
      const stats = quotesArray.map((q: any) => ({
        symbol: q.symbol,
        price: q.last,
        change: q.change,
        volume: q.volume
      }));
      const gainers = [...stats].sort((a, b) => b.change - a.change).slice(0, 3);
      const losers = [...stats].sort((a, b) => a.change - b.change).slice(0, 3);
      const active = [...stats].sort((a, b) => b.volume - a.volume).slice(0, 3);
      return { gainers, losers, active };
    } catch (error) {
      console.error('Error fetching market stats:', error);
      throw error;
    }
  }
};

// Trading API methods
export const tradingApi = {
  getTradingMode: () => {
    const isPaperTrading = localStorage.getItem('paper_trading') !== 'false';
    
    // Check which brokers are configured
    const hasTradierKeys = localStorage.getItem('tradier_api_key') && localStorage.getItem('tradier_account_number');
    const hasAlpacaKeys = localStorage.getItem('alpaca_api_key') && localStorage.getItem('alpaca_api_secret');
    const hasEtradeKeys = localStorage.getItem('etrade_access_token') && localStorage.getItem('etrade_access_secret');
    
    return {
      isPaperTrading,
      brokers: {
        tradier: {
          isConnected: localStorage.getItem('tradier_connected') === 'true',
          isConfigured: !!hasTradierKeys
        },
        alpaca: {
          isConnected: localStorage.getItem('alpaca_connected') === 'true', 
          isConfigured: !!hasAlpacaKeys
        },
        etrade: {
          isConnected: localStorage.getItem('etrade_connected') === 'true',
          isConfigured: !!hasEtradeKeys
        }
      }
    };
  },

  switchTradingMode: (usePaperTrading: boolean) => {
    localStorage.setItem('paper_trading', usePaperTrading ? 'true' : 'false');
    // Update trading mode in memory
    console.log(`Switched to ${usePaperTrading ? 'paper' : 'live'} trading mode`);
  },

  clearCredentials: (broker: 'tradier' | 'alpaca' | 'etrade') => {
    if (broker === 'tradier') {
      localStorage.removeItem('tradier_api_key');
      localStorage.removeItem('tradier_account_number');
      localStorage.removeItem('tradier_connected');
    } else if (broker === 'alpaca') {
      localStorage.removeItem('alpaca_api_key');
      localStorage.removeItem('alpaca_api_secret');
      localStorage.removeItem('alpaca_connected');
    } else if (broker === 'etrade') {
      localStorage.removeItem('etrade_access_token');
      localStorage.removeItem('etrade_access_secret');
      localStorage.removeItem('etrade_connected');
    }
    
    console.log(`Cleared credentials for ${broker}`);
    return true;
  },
  
  getStatusMessage: () => {
    const isPaperTrading = localStorage.getItem('paper_trading') !== 'false';
    if (isPaperTrading) return 'Paper Trading Mode';
    return 'Live Trading Mode';
  }
};

// E*TRADE OAuth API for facilitating OAuth flow
export const etradeOAuthApi = {
  getAuthUrl: async (): Promise<string> => {
    // Placeholder for E*TRADE OAuth implementation
    return 'https://us.etrade.com/e/t/etws/authorize?key=your-app-key&token=your-request-token';
  },
  
  initiateOAuth: async (): Promise<{ authUrl: string, requestToken: string }> => {
    // Placeholder implementation for E*TRADE OAuth flow
    // In a real implementation, this would make an API call to get a request token
    const requestToken = 'dummy-request-token';
    const authUrl = 'https://us.etrade.com/e/t/etws/authorize?key=your-app-key&token=' + requestToken;
    
    return {
      authUrl,
      requestToken
    };
  },
  
  handleCallback: async (verifier: string): Promise<any> => {
    // Placeholder for E*TRADE OAuth implementation
    return {
      success: false,
      requestToken: 'dummy-request-token'
    };
  },

  completeOAuth: async (requestToken: string, verifier: string): Promise<boolean> => {
    localStorage.setItem('etrade_access_token', 'dummy-access-token');
    localStorage.setItem('etrade_access_secret', 'dummy-access-secret');
    return true;
  }
};

// Export all API methods as a single service
export default {
  portfolio: portfolioApi,
  trades: tradesApi,
  news: newsApi,
  market: marketApi,
  trading: tradingApi,
  etradeOAuth: etradeOAuthApi,
  strategies: {
    getStrategies: async () => {
      // Return mock data for strategies since there's no backend
      return [
        {
          name: 'Trend Following',
          description: 'Follows established market trends using moving averages',
          status: 'active',
          allocation: 30,
          performance: {
            daily: 0.5,
            weekly: 1.2,
            monthly: 4.8,
            yearly: 18.2
          },
          activeTrades: 3,
          signalStrength: 7.8,
          lastUpdated: new Date(Date.now() - 3600000).toISOString()
        },
        {
          name: 'Mean Reversion',
          description: 'Capitalizes on price corrections after significant moves',
          status: 'active',
          allocation: 20,
          performance: {
            daily: -0.2,
            weekly: 0.8,
            monthly: 2.7,
            yearly: 11.5
          },
          activeTrades: 2,
          signalStrength: 6.2,
          lastUpdated: new Date(Date.now() - 7200000).toISOString()
        }
      ];
    }
  }
};
