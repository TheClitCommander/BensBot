import React from 'react';

const PerformanceMetrics = () => {
  // Mock data for top performing strategies
  const topStrategies = [
    {
      id: 'ST-412',
      name: 'Smart Beta Multi-Factor',
      type: 'Stocks',
      metrics: {
        cagr: 18.4,
        sharpe: 1.72,
        maxDrawdown: 9.8,
        winRate: 64.2,
        profitFactor: 2.35
      },
      score: 92
    },
    {
      id: 'ST-389',
      name: 'Volatility Regime Switching',
      type: 'Multi-asset',
      metrics: {
        cagr: 15.7,
        sharpe: 1.68,
        maxDrawdown: 11.3,
        winRate: 58.7,
        profitFactor: 2.12
      },
      score: 89
    },
    {
      id: 'ST-408',
      name: 'Crypto Market Neutral',
      type: 'Crypto',
      metrics: {
        cagr: 24.3,
        sharpe: 1.54,
        maxDrawdown: 15.2,
        winRate: 52.1,
        profitFactor: 1.95
      },
      score: 85
    }
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h2>Performance Metrics</h2>
        <select 
          style={{ 
            backgroundColor: '#333', 
            color: 'white', 
            border: 'none', 
            padding: '5px 10px',
            borderRadius: '4px'
          }}
        >
          <option value="week">Last 7 Days</option>
          <option value="month">Last 30 Days</option>
          <option value="quarter">Last Quarter</option>
          <option value="year">Last Year</option>
        </select>
      </div>
      
      <div className="card-content">
        <h4 style={{ marginBottom: '12px' }}>Top Performing Strategies</h4>
        
        {topStrategies.map((strategy, index) => (
          <div 
            key={strategy.id}
            style={{ 
              backgroundColor: '#272727',
              borderRadius: '6px',
              padding: '16px',
              marginBottom: '16px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{strategy.name}</h3>
                <div style={{ fontSize: '0.8rem', color: '#9e9e9e', marginTop: '4px' }}>
                  {strategy.type} • ID: {strategy.id}
                </div>
              </div>
              <div 
                style={{ 
                  backgroundColor: '#1e1e1e',
                  borderRadius: '50%',
                  width: '48px',
                  height: '48px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '1.1rem',
                  color: strategy.score >= 90 ? '#4CAF50' : strategy.score >= 80 ? '#FF9800' : '#F44336'
                }}
              >
                {strategy.score}
              </div>
            </div>
            
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ minWidth: '80px' }}>
                <div className={`${strategy.metrics.cagr >= 15 ? 'positive-value' : ''}`} style={{ fontWeight: 'bold' }}>
                  {strategy.metrics.cagr}%
                </div>
                <div style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>CAGR</div>
              </div>
              <div style={{ minWidth: '80px' }}>
                <div style={{ fontWeight: 'bold' }}>{strategy.metrics.sharpe}</div>
                <div style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>Sharpe</div>
              </div>
              <div style={{ minWidth: '80px' }}>
                <div className="negative-value" style={{ fontWeight: 'bold' }}>
                  {strategy.metrics.maxDrawdown}%
                </div>
                <div style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>Max DD</div>
              </div>
              <div style={{ minWidth: '80px' }}>
                <div style={{ fontWeight: 'bold' }}>{strategy.metrics.winRate}%</div>
                <div style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>Win Rate</div>
              </div>
              <div style={{ minWidth: '80px' }}>
                <div style={{ fontWeight: 'bold' }}>{strategy.metrics.profitFactor}</div>
                <div style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>Profit Factor</div>
              </div>
            </div>
            
            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button 
                style={{ 
                  backgroundColor: 'transparent', 
                  border: '1px solid #4F8BFF', 
                  color: '#4F8BFF', 
                  padding: '4px 10px', 
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                View Details
              </button>
              <button 
                style={{ 
                  backgroundColor: '#4F8BFF', 
                  border: 'none',
                  color: 'white', 
                  padding: '4px 10px', 
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Deploy Strategy
              </button>
            </div>
          </div>
        ))}
        
        <div style={{ textAlign: 'center', marginTop: '8px' }}>
          <button
            style={{
              backgroundColor: 'transparent',
              border: '1px solid #9e9e9e',
              color: '#9e9e9e',
              padding: '6px 16px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            View All Strategies
          </button>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMetrics;
