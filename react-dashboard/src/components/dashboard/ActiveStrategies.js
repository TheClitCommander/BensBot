import React from 'react';

const ActiveStrategies = () => {
  // Mock data - would be connected to your trading engine
  const strategiesData = [
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
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h2>Active Strategies</h2>
        <select 
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
              {strategiesData.map((strategy) => (
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ActiveStrategies;
