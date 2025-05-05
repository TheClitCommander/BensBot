import React from 'react';

interface MarketNewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
  summary: string;
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  impact: 'High' | 'Medium' | 'Low';
  category: string;
  relatedAssets: string[];
}

const MarketOverview: React.FC = () => {
  // Mock data for market news
  const marketNews: MarketNewsItem[] = [
    {
      id: 'news-1',
      title: 'Fed Signals Potential Rate Cut in Next Meeting',
      source: 'Bloomberg',
      time: '2025-05-04T13:45:00',
      summary: 'Federal Reserve officials indicated a potential rate cut in the next FOMC meeting, citing improving inflation data and stable employment figures.',
      sentiment: 'Positive',
      impact: 'High',
      category: 'Monetary Policy',
      relatedAssets: ['SPY', 'TLT', 'GLD', 'USD']
    },
    {
      id: 'news-2',
      title: 'Tech Earnings Exceed Expectations, Boosting Market Sentiment',
      source: 'CNBC',
      time: '2025-05-04T11:20:00',
      summary: 'Major tech companies including Apple, Microsoft, and Amazon reported earnings that exceeded analyst expectations, pushing the Nasdaq to new highs.',
      sentiment: 'Positive',
      impact: 'High',
      category: 'Earnings',
      relatedAssets: ['QQQ', 'AAPL', 'MSFT', 'AMZN']
    },
    {
      id: 'news-3',
      title: 'Oil Prices Decline on Increased Production Announcement',
      source: 'Reuters',
      time: '2025-05-04T09:30:00',
      summary: 'Crude oil prices dropped after OPEC+ announced plans to increase production starting next month, easing supply concerns.',
      sentiment: 'Negative',
      impact: 'Medium',
      category: 'Commodities',
      relatedAssets: ['USO', 'XLE', 'CVX', 'XOM']
    },
    {
      id: 'news-4',
      title: "Europe's Manufacturing PMI Shows Expansion for Third Consecutive Month",
      source: 'Financial Times',
      time: '2025-05-04T08:15:00',
      summary: 'European manufacturing activity continued to expand, with the PMI reading at 53.2, indicating economic resilience despite ongoing challenges.',
      sentiment: 'Positive',
      impact: 'Medium',
      category: 'Economic Data',
      relatedAssets: ['VGK', 'FEZ', 'HEDJ', 'EUR']
    },
    {
      id: 'news-5',
      title: 'Bitcoin Surpasses $78,000 as Institutional Adoption Accelerates',
      source: 'CoinDesk',
      time: '2025-05-04T07:45:00',
      summary: 'Bitcoin reached a new all-time high, surpassing $78,000 as institutional investors continue to increase their crypto allocations.',
      sentiment: 'Positive',
      impact: 'Medium',
      category: 'Crypto',
      relatedAssets: ['BTC-USD', 'ETH-USD', 'COIN', 'MSTR']
    }
  ];

  // Get sentiment badge color
  const getSentimentBadgeColor = (sentiment: 'Positive' | 'Negative' | 'Neutral'): string => {
    switch (sentiment) {
      case 'Positive':
        return 'success';
      case 'Negative':
        return 'danger';
      case 'Neutral':
        return 'info';
      default:
        return 'info';
    }
  };

  // Get impact badge color
  const getImpactBadgeColor = (impact: 'High' | 'Medium' | 'Low'): string => {
    switch (impact) {
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

  // Format time
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>Market Sentiment Analysis</h2>
            <select 
              style={{ 
                backgroundColor: '#333', 
                color: 'white', 
                border: 'none', 
                padding: '5px 10px',
                borderRadius: '4px'
              }}
            >
              <option value="ai">AI Analysis</option>
              <option value="technical">Technical</option>
              <option value="fundamental">Fundamental</option>
            </select>
          </div>
          
          <div className="card-content">
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3 style={{ marginTop: 0 }}>Market Summary</h3>
              <p>
                Today's market is showing <strong className="positive-value">bullish sentiment</strong> with tech and financial sectors leading gains. 
                The Federal Reserve's recent commentary has boosted investor confidence, while strong earnings reports continue to support market momentum.
              </p>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', margin: '20px 0' }}>
                <div>
                  <h4 style={{ margin: '0 0 8px 0' }}>Sector Performance</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    <table style={{ width: '100%', fontSize: '0.9rem' }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: 'left' }}>Sector</th>
                          <th style={{ textAlign: 'right' }}>Change</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>Technology</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+2.34%</td>
                        </tr>
                        <tr>
                          <td>Financials</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+1.67%</td>
                        </tr>
                        <tr>
                          <td>Healthcare</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+0.89%</td>
                        </tr>
                        <tr>
                          <td>Communication</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+0.75%</td>
                        </tr>
                        <tr>
                          <td>Consumer Cyclical</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+0.52%</td>
                        </tr>
                        <tr>
                          <td>Industrials</td>
                          <td style={{ color: '#4CAF50', textAlign: 'right' }}>+0.31%</td>
                        </tr>
                        <tr>
                          <td>Real Estate</td>
                          <td style={{ color: '#F44336', textAlign: 'right' }}>-0.24%</td>
                        </tr>
                        <tr>
                          <td>Utilities</td>
                          <td style={{ color: '#F44336', textAlign: 'right' }}>-0.35%</td>
                        </tr>
                        <tr>
                          <td>Energy</td>
                          <td style={{ color: '#F44336', textAlign: 'right' }}>-1.42%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div style={{ marginLeft: '40px' }}>
                  <h4 style={{ margin: '0 0 8px 0' }}>Key Factors</h4>
                  <ul style={{ padding: '0 0 0 20px', margin: 0 }}>
                    <li style={{ marginBottom: '10px' }}>
                      <strong>Fed Policy:</strong> <span className="badge success">Bullish</span><br/>
                      <span style={{ fontSize: '0.85rem' }}>Rate cut signals driving market optimism</span>
                    </li>
                    <li style={{ marginBottom: '10px' }}>
                      <strong>Earnings:</strong> <span className="badge success">Bullish</span><br/>
                      <span style={{ fontSize: '0.85rem' }}>Q2 reports exceeding expectations</span>
                    </li>
                    <li style={{ marginBottom: '10px' }}>
                      <strong>Economic Data:</strong> <span className="badge success">Bullish</span><br/>
                      <span style={{ fontSize: '0.85rem' }}>Employment and manufacturing data positive</span>
                    </li>
                    <li style={{ marginBottom: '10px' }}>
                      <strong>Volatility:</strong> <span className="badge warning">Neutral</span><br/>
                      <span style={{ fontSize: '0.85rem' }}>VIX at 14.32, relatively low</span>
                    </li>
                    <li style={{ marginBottom: '10px' }}>
                      <strong>Oil Prices:</strong> <span className="badge danger">Bearish</span><br/>
                      <span style={{ fontSize: '0.85rem' }}>Declining on increased production</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h2 className="card-header">Key Market Events</h2>
          <div className="card-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <select 
                  style={{ 
                    backgroundColor: '#333', 
                    color: 'white', 
                    border: 'none', 
                    padding: '5px 10px',
                    borderRadius: '4px',
                    marginRight: '8px'
                  }}
                >
                  <option value="all">All Categories</option>
                  <option value="monetary">Monetary Policy</option>
                  <option value="earnings">Earnings</option>
                  <option value="economic">Economic Data</option>
                  <option value="geopolitical">Geopolitical</option>
                </select>
                <select 
                  style={{ 
                    backgroundColor: '#333', 
                    color: 'white', 
                    border: 'none', 
                    padding: '5px 10px',
                    borderRadius: '4px'
                  }}
                >
                  <option value="all">All Impact</option>
                  <option value="high">High Impact</option>
                  <option value="medium">Medium Impact</option>
                  <option value="low">Low Impact</option>
                </select>
              </div>
              <div>
                <input 
                  type="text" 
                  placeholder="Search news..." 
                  style={{
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '5px 10px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {marketNews.map((news) => (
                <div 
                  key={news.id}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>{news.title}</h3>
                    <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>
                      {formatTime(news.time)}
                    </div>
                  </div>
                  
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e', marginBottom: '8px' }}>
                    Source: {news.source} | Category: {news.category}
                  </div>
                  
                  <p style={{ margin: '8px 0', fontSize: '0.9rem' }}>
                    {news.summary}
                  </p>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span className={`badge ${getSentimentBadgeColor(news.sentiment)}`}>
                        {news.sentiment}
                      </span>
                      <span className={`badge ${getImpactBadgeColor(news.impact)}`}>
                        {news.impact} Impact
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '0.8rem' }}>
                      {news.relatedAssets.slice(0, 3).join(', ')}
                      {news.relatedAssets.length > 3 && '...'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;
