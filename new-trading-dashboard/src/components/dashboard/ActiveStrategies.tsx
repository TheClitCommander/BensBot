import React, { useState, useEffect } from 'react';
import { strategiesApi, StrategyData } from '../../services/api';

interface Strategy {
  id: string;
  name: string;
  type: 'Stocks' | 'Options' | 'Crypto' | 'Forex';
  status: 'Active' | 'Paused' | 'Stopped';
  performance: number;
  allocation: number;
  symbols: string[];
  lastSignal: string;
  signalType: 'Buy' | 'Sell' | 'Hold';
}

const ActiveStrategies: React.FC = () => {
  const [strategiesData, setStrategiesData] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  
  // Fetch strategies data from API
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        setLoading(true);
        const data = await strategiesApi.getStrategies();
        
        // Transform API data to our component format
        const transformedData: Strategy[] = data.map((item: StrategyData, index: number) => ({
          id: `ST-${index + 100}`,
          name: item.name,
          type: determineStrategyType(item.name),
          status: item.status === 'active' ? 'Active' : 'Paused',
          performance: item.performance.monthly,
          allocation: item.allocation,
          symbols: [],  // API doesn't provide symbols, could be enhanced
          lastSignal: item.lastUpdated,
          signalType: determineSignalType(item.performance.daily)
        }));
        
        setStrategiesData(transformedData);
        setError(null);
      } catch (err) {
        console.error('Error fetching strategies data:', err);
        setError('Failed to load strategies data');
        
        // If we have no data yet, set fallback mock data
        if (strategiesData.length === 0) {
          setStrategiesData([
    {
      id: 'ST-241',
      name: 'Mean Reversion ETF',
      type: 'Stocks',
      status: 'Active',
      performance: 15.7,
      allocation: 12.5,
      symbols: ['SPY', 'QQQ', 'IWM', 'DIA'],
      lastSignal: '2025-05-03 09:34:21',
      signalType: 'Buy'
    },
    {
      id: 'ST-156',
      name: 'Tech Momentum',
      type: 'Stocks',
      status: 'Active',
      performance: 21.3,
      allocation: 18.0,
      symbols: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'],
      lastSignal: '2025-05-04 10:12:34',
      signalType: 'Hold'
    },
    {
      id: 'ST-312',
      name: 'BTC Volatility Edge',
      type: 'Crypto',
      status: 'Active',
      performance: 32.1,
      allocation: 15.0,
      symbols: ['BTC-USD', 'ETH-USD'],
      lastSignal: '2025-05-04 11:45:00',
      signalType: 'Buy'
    },
    {
      id: 'ST-127',
      name: 'Forex Range Trader',
      type: 'Forex',
      status: 'Active',
      performance: 8.4,
      allocation: 10.5,
      symbols: ['EUR/USD', 'GBP/USD', 'USD/JPY'],
      lastSignal: '2025-05-02 14:22:51',
      signalType: 'Sell'
    },
    {
      id: 'ST-198',
      name: 'Options Income',
      type: 'Options',
      status: 'Active',
      performance: 12.1,
      allocation: 15.0,
      symbols: ['SPY', 'QQQ', 'AAPL', 'TSLA'],
      lastSignal: '2025-05-04 09:30:15',
      signalType: 'Sell'
    }
          ]);
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchStrategies();
    
    // Refresh every 60 seconds
    const intervalId = setInterval(fetchStrategies, 60000);
    
    return () => clearInterval(intervalId);
  }, []);
  
  // Helper function to determine strategy type based on name
  const determineStrategyType = (name: string): 'Stocks' | 'Options' | 'Crypto' | 'Forex' => {
    const nameLower = name.toLowerCase();
    if (nameLower.includes('option') || nameLower.includes('iron') || nameLower.includes('spread')) {
      return 'Options';
    } else if (nameLower.includes('btc') || nameLower.includes('eth') || nameLower.includes('crypto')) {
      return 'Crypto';
    } else if (nameLower.includes('forex') || nameLower.includes('eur/usd') || nameLower.includes('currency')) {
      return 'Forex';
    }
    return 'Stocks';  // Default type
  };
  
  // Helper function to determine signal type based on daily performance
  const determineSignalType = (dailyPerformance: number): 'Buy' | 'Sell' | 'Hold' => {
    if (dailyPerformance > 0.5) {
      return 'Buy';
    } else if (dailyPerformance < -0.5) {
      return 'Sell';
    }
    return 'Hold';
  };
  
  // Filter strategies based on selected type
  const filteredStrategies = filter === 'all' 
    ? strategiesData 
    : strategiesData.filter(strategy => strategy.type.toLowerCase() === filter);
  
  // Show loading state
  if (loading && strategiesData.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>Active Strategies</h2>
        </div>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0' }}>
          <div>Loading strategies data...</div>
        </div>
      </div>
    );
  }
  
  // Show error state
  if (error && strategiesData.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>Active Strategies</h2>
        </div>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0', color: '#f87171' }}>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>Active Strategies</h2>
        <select 
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ 
            backgroundColor: '#333', 
            color: 'white', 
            border: 'none', 
            padding: '5px 10px',
            borderRadius: '4px'
          }}
        >
          <option value="all">All Types</option>
          <option value="stocks">Stocks</option>
          <option value="options">Options</option>
          <option value="crypto">Crypto</option>
          <option value="forex">Forex</option>
        </select>
      </div>
      
      <div className="card-content">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Type</th>
                <th>Performance</th>
                <th>Allocation</th>
                <th>Last Signal</th>
              </tr>
            </thead>
            <tbody>
              {filteredStrategies.length > 0 ? filteredStrategies.map((strategy) => (
                <tr key={strategy.id}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 500 }}>{strategy.name}</span>
                      <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>
                        {strategy.symbols.slice(0, 3).join(', ')}
                        {strategy.symbols.length > 3 ? `, +${strategy.symbols.length - 3} more` : ''}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${
                      strategy.type === 'Stocks' ? 'info' : 
                      strategy.type === 'Options' ? 'warning' :
                      strategy.type === 'Crypto' ? 'success' : 'danger'
                    }`}>
                      {strategy.type}
                    </span>
                  </td>
                  <td className={strategy.performance >= 0 ? 'positive-value' : 'negative-value'}>
                    {strategy.performance >= 0 ? '+' : ''}{strategy.performance}%
                  </td>
                  <td>{strategy.allocation}%</td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span className={`badge ${
                        strategy.signalType === 'Buy' ? 'success' : 
                        strategy.signalType === 'Sell' ? 'danger' : 'warning'
                      }`} style={{ alignSelf: 'flex-start' }}>
                        {strategy.signalType}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#9e9e9e', marginTop: '4px' }}>
                        {new Date(strategy.lastSignal).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '20px 0' }}>
                    No strategies match the current filter
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ActiveStrategies;
