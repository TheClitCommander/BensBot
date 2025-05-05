import React from 'react';

const MarketOverview = () => {
  // Mock data - would be connected to your market data API
  const marketData = [
    { name: 'S&P 500', symbol: 'SPY', price: 532.45, change: 4.21, changePercent: 0.8 },
    { name: 'Nasdaq', symbol: 'QQQ', price: 475.82, change: 6.34, changePercent: 1.35 },
    { name: 'Dow Jones', symbol: 'DIA', price: 421.63, change: 2.15, changePercent: 0.51 },
    { name: 'Russell 2000', symbol: 'IWM', price: 246.18, change: -1.24, changePercent: -0.5 },
    { name: 'Bitcoin', symbol: 'BTC-USD', price: 78245.32, change: 1243.56, changePercent: 1.61 },
    { name: 'Ethereum', symbol: 'ETH-USD', price: 3856.45, change: 87.32, changePercent: 2.32 }
  ];

  // Market stats
  const marketStats = [
    { name: 'VIX', value: 14.32, change: -0.45, status: 'low' },
    { name: 'US 10Y', value: 3.42, change: 0.03, status: 'neutral' },
    { name: 'Gold', value: 2354.12, change: 12.45, status: 'high' },
    { name: 'Oil WTI', value: 78.45, change: -0.87, status: 'low' }
  ];

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
            <span>Bullish</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-bar-fill success" 
              style={{ width: '72%' }}
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
