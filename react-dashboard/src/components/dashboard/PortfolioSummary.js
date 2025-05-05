import React from 'react';

const PortfolioSummary = () => {
  // Mock data - would be connected to your trading engine in production
  const portfolioData = {
    totalValue: 852437.29,
    dailyChange: 12483.57,
    dailyChangePercent: 1.49,
    monthlyReturn: 7.2,
    allocation: [
      { category: 'Stocks', value: 45, color: '#4F8BFF' },
      { category: 'Options', value: 15, color: '#FF9800' },
      { category: 'Crypto', value: 25, color: '#4CAF50' },
      { category: 'Forex', value: 10, color: '#F44336' },
      { category: 'Cash', value: 5, color: '#9E9E9E' }
    ]
  };

  return (
    <div className="card">
      <h2 className="card-header">Portfolio Summary</h2>
      <div className="card-content">
        <div className="stats-container">
          <div className="stat-item">
            <div className="stat-value">${portfolioData.totalValue.toLocaleString()}</div>
            <div className="stat-label">Total Value</div>
          </div>
          <div className="stat-item">
            <div className={`stat-value ${portfolioData.dailyChange >= 0 ? 'positive-value' : 'negative-value'}`}>
              {portfolioData.dailyChange >= 0 ? '+' : ''}${portfolioData.dailyChange.toLocaleString()} 
              ({portfolioData.dailyChangePercent >= 0 ? '+' : ''}{portfolioData.dailyChangePercent}%)
            </div>
            <div className="stat-label">Daily Change</div>
          </div>
          <div className="stat-item">
            <div className={`stat-value ${portfolioData.monthlyReturn >= 0 ? 'positive-value' : 'negative-value'}`}>
              {portfolioData.monthlyReturn >= 0 ? '+' : ''}{portfolioData.monthlyReturn}%
            </div>
            <div className="stat-label">Monthly Return</div>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.75rem' }}>Asset Allocation</h4>
          <div style={{ display: 'flex', height: '30px', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.75rem' }}>
            {portfolioData.allocation.map((asset, index) => (
              <div 
                key={index} 
                style={{ 
                  width: `${asset.value}%`, 
                  backgroundColor: asset.color,
                  transition: 'width 0.3s ease'
                }} 
              />
            ))}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {portfolioData.allocation.map((asset, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '12px', height: '12px', backgroundColor: asset.color, borderRadius: '2px' }} />
                <span style={{ fontSize: '0.875rem' }}>{asset.category} ({asset.value}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummary;
