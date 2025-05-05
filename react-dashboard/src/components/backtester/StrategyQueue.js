import React from 'react';

const StrategyQueue = () => {
  // Mock data for strategies in queue
  const strategyQueue = [
    {
      id: 'ST-427',
      name: 'ML-Enhanced Mean Reversion',
      status: 'In Queue',
      priority: 'High',
      estimatedStart: '2025-05-04 15:30:00',
      assets: ['SPY', 'QQQ', 'IWM'],
      complexity: 'High'
    },
    {
      id: 'ST-428',
      name: 'Adaptive Momentum with Volatility Control',
      status: 'In Queue',
      priority: 'Medium',
      estimatedStart: '2025-05-04 16:15:00',
      assets: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'],
      complexity: 'Medium'
    },
    {
      id: 'ST-429',
      name: 'Multi-timeframe Breakout Detection',
      status: 'In Queue',
      priority: 'Medium',
      estimatedStart: '2025-05-04 17:00:00',
      assets: ['BTC-USD', 'ETH-USD', 'SOL-USD'],
      complexity: 'High'
    },
    {
      id: 'ST-430',
      name: 'Sector Rotation Algorithm',
      status: 'In Queue',
      priority: 'Low',
      estimatedStart: '2025-05-04 18:30:00',
      assets: ['XLF', 'XLK', 'XLE', 'XLV', 'XLP', 'XLI', 'XLY', 'XLB', 'XLU', 'XLRE', 'XLC'],
      complexity: 'High'
    }
  ];

  // Get badge color based on priority
  const getPriorityBadgeColor = (priority) => {
    switch (priority) {
      case 'High':
        return 'danger';
      case 'Medium':
        return 'warning';
      case 'Low':
        return 'info';
      default:
        return 'info';
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Strategy Queue</h2>
        <select 
          style={{ 
            backgroundColor: '#333', 
            color: 'white', 
            border: 'none', 
            padding: '5px 10px',
            borderRadius: '4px'
          }}
        >
          <option value="all">All Priorities</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
      </div>
      
      <div className="card-content">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Priority</th>
                <th>Est. Start Time</th>
                <th>Complexity</th>
              </tr>
            </thead>
            <tbody>
              {strategyQueue.map((strategy) => (
                <tr key={strategy.id}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 500 }}>{strategy.name}</span>
                      <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>
                        {strategy.assets.slice(0, 3).join(', ')}
                        {strategy.assets.length > 3 ? `, +${strategy.assets.length - 3} more` : ''}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${getPriorityBadgeColor(strategy.priority)}`}>
                      {strategy.priority}
                    </span>
                  </td>
                  <td>
                    {new Date(strategy.estimatedStart).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td>{strategy.complexity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
          <span style={{ fontSize: '0.875rem', color: '#9e9e9e' }}>
            4 strategies in queue
          </span>
          <div>
            <button style={{ 
              backgroundColor: '#4F8BFF', 
              color: 'white', 
              border: 'none', 
              padding: '6px 12px', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}>
              Submit New Strategy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyQueue;
