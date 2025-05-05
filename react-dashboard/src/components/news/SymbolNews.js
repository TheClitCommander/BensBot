import React, { useState } from 'react';

const SymbolNews = () => {
  const [searchSymbol, setSearchSymbol] = useState('AAPL');
  
  // Mock data for symbol news
  const symbolNewsData = {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    currentPrice: 198.45,
    change: 3.27,
    changePercent: 1.68,
    market: 'NASDAQ',
    sentiment: 'Bullish',
    volatility: 'Medium',
    marketCap: '3.15T',
    peRatio: 32.8,
    analystRating: 'Buy',
    news: [
      {
        id: 'news-1',
        title: 'Apple Reports Record Services Revenue in Latest Quarter',
        source: 'Wall Street Journal',
        time: '2025-05-04T11:32:00',
        summary: 'Apple's services segment, which includes App Store, Apple Music, and Apple TV+, saw record revenue in the latest quarter, offsetting slower iPhone sales growth.',
        sentiment: 'Positive',
        impact: 'Medium'
      },
      {
        id: 'news-2',
        title: 'Apple Unveils New AI Features Coming to iOS 19',
        source: 'The Verge',
        time: '2025-05-04T09:15:00',
        summary: 'At its developer conference, Apple introduced a suite of new AI features for iOS 19, including enhanced Siri capabilities and on-device machine learning tools.',
        sentiment: 'Positive',
        impact: 'High'
      },
      {
        id: 'news-3',
        title: 'Apple Expands Manufacturing in India, Reducing China Dependency',
        source: 'Bloomberg',
        time: '2025-05-03T14:45:00',
        summary: 'Apple is significantly expanding its manufacturing operations in India, a move analysts see as reducing its dependency on China amid ongoing supply chain challenges.',
        sentiment: 'Positive',
        impact: 'Medium'
      },
      {
        id: 'news-4',
        title: 'European Commission Launches New Investigation into Apple App Store Practices',
        source: 'Reuters',
        time: '2025-05-03T08:30:00',
        summary: 'The European Commission has launched a new antitrust investigation into Apple's App Store practices, focusing on recent changes to developer fees.',
        sentiment: 'Negative',
        impact: 'Medium'
      },
      {
        id: 'news-5',
        title: 'Apple Supplier Report Indicates Potential iPhone Production Delays',
        source: 'Nikkei Asia',
        time: '2025-05-02T22:15:00',
        summary: 'A report from a key Apple supplier suggests potential production delays for the upcoming iPhone models due to component shortages.',
        sentiment: 'Negative',
        impact: 'Medium'
      }
    ],
    aiInsights: [
      {
        title: 'Increasing Services Revenue',
        analysis: 'Apple's pivot toward services continues to show strong results, with services revenue growing at 18% YoY. This shift helps reduce dependency on hardware sales cycles and provides more stable, recurring revenue streams.',
        impact: 'Positive for long-term growth prospects'
      },
      {
        title: 'AI Strategy',
        analysis: 'Apple's new AI features position it competitively in the ongoing AI race with Google and Microsoft. The focus on on-device processing aligns with Apple's privacy-first approach and differentiates its offerings.',
        impact: 'Potentially significant for product differentiation'
      },
      {
        title: 'Supply Chain Diversification',
        analysis: 'The expansion in India represents a strategic diversification of manufacturing, reducing geopolitical risks associated with China dependency.',
        impact: 'Reduces long-term operational risks'
      },
      {
        title: 'Regulatory Pressure',
        analysis: 'Ongoing regulatory scrutiny in Europe could impact App Store revenue model, potentially forcing changes to Apple's 15-30% commission structure.',
        impact: 'Represents a significant regulatory risk'
      }
    ]
  };

  // Get sentiment badge color
  const getSentimentBadgeColor = (sentiment) => {
    switch (sentiment) {
      case 'Positive':
      case 'Bullish':
        return 'success';
      case 'Negative':
      case 'Bearish':
        return 'danger';
      case 'Neutral':
        return 'info';
      default:
        return 'info';
    }
  };

  // Get impact badge color
  const getImpactBadgeColor = (impact) => {
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
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Handle symbol search
  const handleSymbolSearch = (e) => {
    e.preventDefault();
    // In a real application, this would fetch data for the new symbol
    console.log(`Searching for symbol: ${searchSymbol}`);
  };

  return (
    <div>
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>Symbol Analysis</h2>
            <form onSubmit={handleSymbolSearch} style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                value={searchSymbol}
                onChange={(e) => setSearchSymbol(e.target.value)}
                placeholder="Enter symbol..." 
                style={{
                  backgroundColor: '#333',
                  border: 'none',
                  padding: '5px 10px',
                  borderRadius: '4px',
                  color: 'white'
                }}
              />
              <button
                type="submit"
                style={{
                  backgroundColor: '#4F8BFF',
                  border: 'none',
                  padding: '5px 10px',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                <span className="material-icons" style={{ fontSize: '18px', verticalAlign: 'middle' }}>search</span>
              </button>
            </form>
          </div>
          
          <div className="card-content">
            <div style={{ 
              padding: '20px',
              backgroundColor: '#272727',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: 0 }}>{symbolNewsData.name} ({symbolNewsData.symbol})</h2>
                  <div style={{ color: '#9e9e9e', marginTop: '4px' }}>
                    {symbolNewsData.market} • Market Cap: ${symbolNewsData.marketCap} • P/E: {symbolNewsData.peRatio}
                  </div>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>${symbolNewsData.currentPrice}</div>
                  <div 
                    className={symbolNewsData.change >= 0 ? 'positive-value' : 'negative-value'}
                    style={{ fontWeight: 'bold' }}
                  >
                    {symbolNewsData.change >= 0 ? '+' : ''}{symbolNewsData.change} 
                    ({symbolNewsData.change >= 0 ? '+' : ''}{symbolNewsData.changePercent}%)
                  </div>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <span className={`badge ${getSentimentBadgeColor(symbolNewsData.sentiment)}`}>
                    {symbolNewsData.sentiment}
                  </span>
                </div>
                <div>
                  <span className="badge info">
                    {symbolNewsData.volatility} Volatility
                  </span>
                </div>
                <div>
                  <span className={`badge ${
                    symbolNewsData.analystRating === 'Buy' ? 'success' :
                    symbolNewsData.analystRating === 'Sell' ? 'danger' : 'warning'
                  }`}>
                    {symbolNewsData.analystRating}
                  </span>
                </div>
              </div>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '16px',
                marginTop: '20px'
              }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>52-Week High</div>
                  <div style={{ fontWeight: 'bold' }}>$205.87</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>52-Week Low</div>
                  <div style={{ fontWeight: 'bold' }}>$157.32</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Avg. Volume</div>
                  <div style={{ fontWeight: 'bold' }}>42.8M</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Dividend Yield</div>
                  <div style={{ fontWeight: 'bold' }}>0.48%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Beta</div>
                  <div style={{ fontWeight: 'bold' }}>1.23</div>
                </div>
              </div>
            </div>
            
            <h3>Latest News</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              {symbolNewsData.news.map((news) => (
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
                    Source: {news.source}
                  </div>
                  
                  <p style={{ margin: '8px 0', fontSize: '0.9rem' }}>
                    {news.summary}
                  </p>
                  
                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <span className={`badge ${getSentimentBadgeColor(news.sentiment)}`}>
                      {news.sentiment}
                    </span>
                    <span className={`badge ${getImpactBadgeColor(news.impact)}`}>
                      {news.impact} Impact
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="card">
          <h2 className="card-header">AI-Generated Insights</h2>
          <div className="card-content">
            <div style={{ padding: '16px', backgroundColor: '#272727', borderRadius: '8px', marginBottom: '20px' }}>
              <h3 style={{ marginTop: 0 }}>Summary</h3>
              <p style={{ lineHeight: '1.5' }}>
                Apple is showing strong momentum with its services business, which is helping offset hardware cyclicality. The company's AI strategy appears promising, although regulatory headwinds in Europe could pose challenges. Supply chain diversification into India is a positive long-term development. Overall sentiment remains bullish despite some near-term production concerns.
              </p>
              
              <div style={{ marginTop: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Overall Sentiment</span>
                  <span>Bullish</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-bar-fill success" 
                    style={{ width: '75%' }}
                  />
                </div>
              </div>
            </div>
            
            <h3>Key Insights</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {symbolNewsData.aiInsights.map((insight, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px'
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: '1rem', marginBottom: '8px' }}>{insight.title}</h3>
                  <p style={{ margin: '0 0 12px 0', fontSize: '0.9rem' }}>
                    {insight.analysis}
                  </p>
                  <div style={{ 
                    fontSize: '0.85rem', 
                    padding: '8px', 
                    backgroundColor: '#1e1e1e', 
                    borderRadius: '4px',
                    borderLeft: '3px solid #4F8BFF'
                  }}>
                    <strong>Impact:</strong> {insight.impact}
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <button
                style={{
                  backgroundColor: '#4F8BFF',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Generate Detailed Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SymbolNews;
