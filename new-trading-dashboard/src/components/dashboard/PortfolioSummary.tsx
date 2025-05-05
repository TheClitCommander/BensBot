import React, { useState, useEffect } from 'react';
import { portfolioApi, PortfolioData } from '../../services/api';

const PortfolioSummary: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get selected portfolio from localStorage
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('alpaca_paper'); // Default to Alpaca
  
  // Fetch portfolio data using the API service
  useEffect(() => {
    // Check if there's a selected portfolio in localStorage
    const storedPortfolio = localStorage.getItem('selectedPortfolio');
    if (storedPortfolio) {
      setSelectedPortfolio(storedPortfolio);
    }
    
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        // Use the existing portfolioApi.getPortfolio method
        // The API will use the broker settings from localStorage
        const data = await portfolioApi.getPortfolio();
        setPortfolioData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching portfolio data:', err);
        setError('Failed to load portfolio data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPortfolioData();
    
    // Refresh every 30 seconds
    const intervalId = setInterval(fetchPortfolioData, 30000);
    
    return () => clearInterval(intervalId);
  }, [selectedPortfolio]);
  
  // Show loading state
  if (loading && !portfolioData) {
    return (
      <div className="card" style={{
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h2 style={{ color: '#e2e8f0', marginTop: 0 }}>Portfolio Summary</h2>
        <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px 0' }}>Loading portfolio data...</div>
      </div>
    );
  }
  
  // Show error state
  if (error && !portfolioData) {
    return (
      <div className="card" style={{
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h2 style={{ color: '#e2e8f0', marginTop: 0 }}>Portfolio Summary</h2>
        <div style={{ color: '#f87171', textAlign: 'center', padding: '30px 0' }}>{error}</div>
      </div>
    );
  }
  
  // Default to fallback data if API data isn't available
  const fallbackData = {
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
    ],
    holdings: [
      { symbol: 'AAPL', name: 'Apple Inc.', quantity: 200, entryPrice: 155.25, currentPrice: 173.75, value: 34750, unrealizedPnl: 3700, unrealizedPnlPercent: 11.89 },
      { symbol: 'MSFT', name: 'Microsoft Corporation', quantity: 100, entryPrice: 287.70, currentPrice: 312.79, value: 31279, unrealizedPnl: 2509, unrealizedPnlPercent: 8.72 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', quantity: 150, entryPrice: 108.42, currentPrice: 124.67, value: 18700.5, unrealizedPnl: 2437.5, unrealizedPnlPercent: 14.99 },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', quantity: 120, entryPrice: 96.30, currentPrice: 109.82, value: 13178.4, unrealizedPnl: 1622.4, unrealizedPnlPercent: 14.04 },
      { symbol: 'TSLA', name: 'Tesla, Inc.', quantity: 75, entryPrice: 235.50, currentPrice: 219.96, value: 16497, unrealizedPnl: -1165.5, unrealizedPnlPercent: -6.59 }
    ]
  };
  
  // Use API data if available, otherwise use fallback data
  const data = portfolioData || fallbackData;

  return (
    <div className="card">
      <h2 className="card-header">Portfolio Summary</h2>
      <div className="card-content">
        <div style={{ marginBottom: '24px' }}>
          {/* Total Value */}
          <div style={{ marginBottom: '20px' }}>
            <div className="stat-value" style={{ fontSize: '2rem', marginBottom: '8px' }}>
              ${data.totalValue.toLocaleString()}
            </div>
            <div className="stat-label">Total Value</div>
          </div>
          
          {/* Daily Change */}
          <div style={{ marginBottom: '20px' }}>
            <div className={`stat-value ${data.dailyChange >= 0 ? 'positive-value' : 'negative-value'}`} style={{ fontSize: '2rem', marginBottom: '4px' }}>
              {data.dailyChange >= 0 ? '+' : ''}${data.dailyChange.toLocaleString()}
            </div>
            <div style={{ fontSize: '1rem' }} className={data.dailyChangePercent >= 0 ? 'positive-value' : 'negative-value'}>
              ({data.dailyChangePercent >= 0 ? '+' : ''}{data.dailyChangePercent}%)
            </div>
            <div className="stat-label" style={{ marginTop: '8px' }}>Daily Change</div>
          </div>
          
          {/* Monthly Return */}
          <div>
            <div className={`stat-value ${data.monthlyReturn >= 0 ? 'positive-value' : 'negative-value'}`} style={{ fontSize: '2rem', marginBottom: '8px' }}>
              {data.monthlyReturn >= 0 ? '+' : ''}{data.monthlyReturn}%
            </div>
            <div className="stat-label">Monthly Return</div>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.75rem' }}>Asset Allocation</h4>
          <div style={{ display: 'flex', height: '30px', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.75rem' }}>
            {portfolioData?.allocation?.map((asset, index) => (
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
            {portfolioData?.allocation?.map((asset, index) => (
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
