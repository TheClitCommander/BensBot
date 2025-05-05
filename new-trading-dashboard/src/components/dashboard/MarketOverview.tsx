import React, { useState, useEffect } from 'react';
import { default as api } from '../../services/api';

// Use the market API from the default export
const marketApi = api.market;

interface MarketDataItem {
  name: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

interface MarketStat {
  name: string;
  value: number;
  change: number;
  status: 'low' | 'neutral' | 'high';
}

const MarketOverview: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketDataItem[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStat[]>([]);
  const [marketSentiment, setMarketSentiment] = useState<string>('Bullish');
  const [sentimentScore, setSentimentScore] = useState<number>(72);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch market data from API
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        
        // Fetch symbol data for key indices and crypto
        const symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'BTC-USD', 'ETH-USD'];
        const marketDataPromises = symbols.map(symbol => marketApi.getSymbolData(symbol));
        
        // Wait for all promises to resolve
        const results = await Promise.allSettled(marketDataPromises);
        
        // Process successful results
        const marketDataItems: MarketDataItem[] = [];
        results.forEach((result, index) => {
          if (result.status === 'fulfilled' && result.value) {
            const symbolData = result.value;
            const symbolName = getSymbolName(symbols[index]);
            marketDataItems.push({
              name: symbolName,
              symbol: symbols[index],
              price: symbolData.price || 0,
              change: symbolData.change || 0,
              changePercent: symbolData.changePercent || 0
            });
          }
        });
        
        // If we didn't get any data or not enough data, use fallback
        if (marketDataItems.length < 3) {
          setMarketData([
    { name: 'S&P 500', symbol: 'SPY', price: 532.45, change: 4.21, changePercent: 0.8 },
    { name: 'Nasdaq', symbol: 'QQQ', price: 475.82, change: 6.34, changePercent: 1.35 },
    { name: 'Dow Jones', symbol: 'DIA', price: 421.63, change: 2.15, changePercent: 0.51 },
    { name: 'Russell 2000', symbol: 'IWM', price: 246.18, change: -1.24, changePercent: -0.5 },
    { name: 'Bitcoin', symbol: 'BTC-USD', price: 78245.32, change: 1243.56, changePercent: 1.61 },
    { name: 'Ethereum', symbol: 'ETH-USD', price: 3856.45, change: 87.32, changePercent: 2.32 }
          ]);
        } else {
          setMarketData(marketDataItems);
        }
        
        // Try to get market stats data
        try {
          const marketStatsData = await marketApi.getMarketStats?.();
          if (marketStatsData && (marketStatsData.gainers.length > 0 || marketStatsData.losers.length > 0 || marketStatsData.active.length > 0)) {
            // Convert market stats data format to what the component expects
            const allStats = [...marketStatsData.gainers, ...marketStatsData.losers, ...marketStatsData.active];
            const transformedStats = allStats.map(stock => ({
              name: stock.symbol,
              value: stock.price,
              change: stock.change,
              status: determineStatus(stock.symbol, stock.price, stock.change)
            }));
            setMarketStats(transformedStats);
            
            // Calculate market sentiment from transformed stats
            const sentiment = calculateMarketSentiment(transformedStats);
            setMarketSentiment(sentiment.sentiment);
            setSentimentScore(sentiment.score);
          } else {
            // Use fallback stats data
            setMarketStats([
    { name: 'VIX', value: 14.32, change: -0.45, status: 'low' },
    { name: 'US 10Y', value: 3.42, change: 0.03, status: 'neutral' },
    { name: 'Gold', value: 2354.12, change: 12.45, status: 'high' },
    { name: 'Oil WTI', value: 78.45, change: -0.87, status: 'low' }
            ]);
          }
        } catch (statsErr) {
          console.error('Error fetching market stats:', statsErr);
          // Use fallback stats data
          setMarketStats([
            { name: 'VIX', value: 14.32, change: -0.45, status: 'low' },
            { name: 'US 10Y', value: 3.42, change: 0.03, status: 'neutral' },
            { name: 'Gold', value: 2354.12, change: 12.45, status: 'high' },
            { name: 'Oil WTI', value: 78.45, change: -0.87, status: 'low' }
          ]);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching market data:', err);
        setError('Failed to load market data');
        
        // If we have no data yet, set fallback data
        if (marketData.length === 0) {
          setMarketData([
            { name: 'S&P 500', symbol: 'SPY', price: 532.45, change: 4.21, changePercent: 0.8 },
            { name: 'Nasdaq', symbol: 'QQQ', price: 475.82, change: 6.34, changePercent: 1.35 },
            { name: 'Dow Jones', symbol: 'DIA', price: 421.63, change: 2.15, changePercent: 0.51 },
            { name: 'Russell 2000', symbol: 'IWM', price: 246.18, change: -1.24, changePercent: -0.5 },
            { name: 'Bitcoin', symbol: 'BTC-USD', price: 78245.32, change: 1243.56, changePercent: 1.61 },
            { name: 'Ethereum', symbol: 'ETH-USD', price: 3856.45, change: 87.32, changePercent: 2.32 }
          ]);
        }
        
        if (marketStats.length === 0) {
          setMarketStats([
            { name: 'VIX', value: 14.32, change: -0.45, status: 'low' },
            { name: 'US 10Y', value: 3.42, change: 0.03, status: 'neutral' },
            { name: 'Gold', value: 2354.12, change: 12.45, status: 'high' },
            { name: 'Oil WTI', value: 78.45, change: -0.87, status: 'low' }
          ]);
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchMarketData();
    
    // Refresh data every 60 seconds
    const intervalId = setInterval(fetchMarketData, 60000);
    
    return () => clearInterval(intervalId);
  }, []);
  
  // Helper function to get full name for symbol
  const getSymbolName = (symbol: string): string => {
    switch (symbol) {
      case 'SPY': return 'S&P 500';
      case 'QQQ': return 'Nasdaq';
      case 'DIA': return 'Dow Jones';
      case 'IWM': return 'Russell 2000';
      case 'BTC-USD': return 'Bitcoin';
      case 'ETH-USD': return 'Ethereum';
      default: return symbol;
    }
  };
  
  // Helper function to determine status based on indicator
  const determineStatus = (name: string, value: number, change: number): 'low' | 'neutral' | 'high' => {
    // VIX interpretation
    if (name === 'VIX') {
      if (value < 15) return 'low';
      if (value > 25) return 'high';
      return 'neutral';
    }
    
    // Yield interpretation
    if (name.includes('10Y') || name.includes('Yield')) {
      if (change > 0.05) return 'high';
      if (change < -0.05) return 'low';
      return 'neutral';
    }
    
    // Generic interpretation based on change
    if (change > 1) return 'high';
    if (change < -1) return 'low';
    return 'neutral';
  };
  
  // Helper function to calculate market sentiment
  const calculateMarketSentiment = (stats: MarketStat[]): { sentiment: string, score: number } => {
    // Count high/low statuses and factor in VIX
    let highCount = 0;
    let lowCount = 0;
    
    stats.forEach(stat => {
      if (stat.name === 'VIX') {
        // VIX is inversely related to sentiment (low VIX = bullish)
        if (stat.status === 'low') highCount += 2;
        if (stat.status === 'high') lowCount += 2;
      } else {
        if (stat.status === 'high') highCount += 1;
        if (stat.status === 'low') lowCount += 1;
      }
    });
    
    const totalPoints = stats.length + 1; // +1 for VIX double counting
    const sentimentScore = Math.min(100, Math.max(0, Math.round((highCount / totalPoints) * 100)));
    
    if (sentimentScore > 65) return { sentiment: 'Bullish', score: sentimentScore };
    if (sentimentScore < 35) return { sentiment: 'Bearish', score: sentimentScore };
    return { sentiment: 'Neutral', score: sentimentScore };
  };
  
  // Show loading state
  if (loading && marketData.length === 0) {
    return (
      <div className="card">
        <h2 className="card-header">Market Overview</h2>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0' }}>
          <div>Loading market data...</div>
        </div>
      </div>
    );
  }
  
  // Show error state
  if (error && marketData.length === 0) {
    return (
      <div className="card">
        <h2 className="card-header">Market Overview</h2>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0', color: '#f87171' }}>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="card-header">Market Overview</h2>
      <div className="card-content">
        <div className="table-container" style={{ marginBottom: '20px' }}>
          <table>
            <thead>
              <tr>
                <th>Index/Asset</th>
                <th>Price</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {marketData.map((item, index) => (
                <tr key={index}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 500 }}>{item.name}</span>
                      <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>{item.symbol}</span>
                    </div>
                  </td>
                  <td>${item.price.toLocaleString()}</td>
                  <td className={item.change >= 0 ? 'positive-value' : 'negative-value'}>
                    {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)} 
                    ({item.change >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <h4>Market Conditions</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginTop: '10px' }}>
          {marketStats.map((stat, index) => (
            <div 
              key={index}
              style={{ 
                flex: '1 1 calc(50% - 15px)',
                minWidth: '120px',
                padding: '10px',
                backgroundColor: '#272727',
                borderRadius: '5px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <div style={{ fontSize: '0.875rem', color: '#9e9e9e' }}>{stat.name}</div>
                <div style={{ fontWeight: 500, marginTop: '3px' }}>
                  {stat.value}
                  <span 
                    className={stat.change >= 0 ? 'positive-value' : 'negative-value'}
                    style={{ fontSize: '0.75rem', marginLeft: '5px' }}
                  >
                    {stat.change >= 0 ? '+' : ''}{stat.change}
                  </span>
                </div>
              </div>
              <div 
                style={{ 
                  width: '10px', 
                  height: '10px', 
                  borderRadius: '50%', 
                  backgroundColor: 
                    stat.status === 'high' ? '#4CAF50' : 
                    stat.status === 'low' ? '#F44336' : 
                    '#FF9800'
                }}
              />
            </div>
          ))}
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
            <span>Market Sentiment</span>
            <span>{marketSentiment}</span>
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-bar-fill ${sentimentScore > 65 ? 'success' : sentimentScore < 35 ? 'danger' : 'warning'}`} 
              style={{ width: `${sentimentScore}%` }}
            />
          </div>
          <div className="progress-bar-labels">
            <span>Bearish</span>
            <span>Neutral</span>
            <span>Bullish</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;
