import React from 'react';

interface OverallImpact {
  score: number;
  status: 'Positive' | 'Negative' | 'Neutral';
  summary: string;
}

interface WatchlistItem {
  symbol: string;
  name: string;
  impact: 'Very Positive' | 'Positive' | 'Neutral' | 'Negative' | 'Very Negative' | 'Neutral to Negative' | 'Neutral to Positive';
  recentNews: string;
  recentEvents: string;
  aiRecommendation: string;
}

interface UpcomingEvent {
  event: string;
  potentialImpact: 'Very High' | 'High' | 'Medium' | 'Low';
  affectedHoldings: string[];
  analysis: string;
}

interface CorrelationFactor {
  factor: string;
  correlation: string;
  explanation: string;
  riskLevel: 'High' | 'Medium' | 'Low';
}

interface PortfolioImpactData {
  overallImpact: OverallImpact;
  watchList: WatchlistItem[];
  upcomingEvents: UpcomingEvent[];
  correlationAnalysis: CorrelationFactor[];
}

const PortfolioImpact: React.FC = () => {
  // Mock data for portfolio impact analysis - in production would connect to news APIs and portfolio data
  // Leverages Alpha Vantage, Marketaux, NewsData.io APIs from config.py
  const portfolioImpactData: PortfolioImpactData = {
    overallImpact: {
      score: 72,
      status: 'Positive',
      summary: 'Recent market events and news show a net positive impact on your portfolio, primarily due to favorable tech sector developments and a more dovish Fed outlook. Your semiconductor and AI-related holdings are particularly well-positioned.'
    },
    watchList: [
      {
        symbol: 'NVDA',
        name: 'NVIDIA Corporation',
        impact: 'Very Positive',
        recentNews: 'Strong AI chip demand and extended market leadership',
        recentEvents: 'Semiconductor industry analysts raised revenue forecasts',
        aiRecommendation: 'Consider increasing position on pullbacks'
      },
      {
        symbol: 'TSLA',
        name: 'Tesla, Inc.',
        impact: 'Neutral to Negative',
        recentNews: 'Production challenges in new factories, increased competition',
        recentEvents: 'Lower than expected deliveries in Asia markets',
        aiRecommendation: 'Monitor closely, potential position reduction if support breaks'
      },
      {
        symbol: 'MSFT',
        name: 'Microsoft Corporation',
        impact: 'Positive',
        recentNews: 'Cloud revenue growth and AI integration momentum',
        recentEvents: 'New enterprise partnerships announced, expanded AI offerings',
        aiRecommendation: 'Maintain current position, potential to add on market weakness'
      }
    ],
    upcomingEvents: [
      {
        event: 'FOMC Meeting Minutes',
        potentialImpact: 'High',
        affectedHoldings: ['SPY', 'QQQ', 'TLT', 'GLD'],
        analysis: 'Dovish tone could benefit your growth stock exposure, while hawkish surprise would pressure technology positions'
      },
      {
        event: 'Tech Earnings Season (Next Week)',
        potentialImpact: 'Very High',
        affectedHoldings: ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT'],
        analysis: 'Your portfolio has 32% exposure to major tech names reporting next week, creating significant near-term volatility risk'
      },
      {
        event: 'CPI Data Release',
        potentialImpact: 'Medium',
        affectedHoldings: ['SPY', 'TLT', 'GLD'],
        analysis: 'Lower than expected inflation could boost your bond holdings and reduce pressure on growth stocks'
      }
    ],
    correlationAnalysis: [
      {
        factor: 'Fed Rate Path',
        correlation: 'Strong Negative',
        explanation: 'Your portfolio has high sensitivity to interest rates due to significant growth stock exposure',
        riskLevel: 'Medium'
      },
      {
        factor: 'AI Technology Adoption',
        correlation: 'Strong Positive',
        explanation: 'Your semiconductor and tech holdings benefit directly from accelerating AI implementation',
        riskLevel: 'Low'
      },
      {
        factor: 'USD Strength',
        correlation: 'Moderate Negative',
        explanation: 'International revenue exposure in your tech holdings creates currency headwinds when dollar strengthens',
        riskLevel: 'Low'
      },
      {
        factor: 'Energy Prices',
        correlation: 'Weak Negative',
        explanation: 'Limited direct exposure, but rising energy costs could pressure consumer discretionary holdings',
        riskLevel: 'Low'
      }
    ]
  };

  return (
    <div>
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">Portfolio News Impact</h2>
          <div className="card-content">
            <div style={{ 
              padding: '20px',
              backgroundColor: '#272727',
              borderRadius: '8px',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '24px'
            }}>
              <div 
                style={{ 
                  backgroundColor: portfolioImpactData.overallImpact.score >= 70 ? '#4CAF5020' : 
                                  portfolioImpactData.overallImpact.score >= 40 ? '#FF980020' : '#F4433620',
                  borderRadius: '50%',
                  width: '80px',
                  height: '80px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}
              >
                <div 
                  style={{ 
                    backgroundColor: '#1e1e1e',
                    borderRadius: '50%',
                    width: '60px',
                    height: '60px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: portfolioImpactData.overallImpact.score >= 70 ? '#4CAF50' : 
                           portfolioImpactData.overallImpact.score >= 40 ? '#FF9800' : '#F44336',
                    fontWeight: 'bold',
                    fontSize: '1.2rem'
                  }}
                >
                  {portfolioImpactData.overallImpact.score}
                </div>
              </div>
              
              <div>
                <h3 style={{ margin: '0 0 8px 0' }}>Overall Impact: <span style={{ 
                  color: portfolioImpactData.overallImpact.status === 'Positive' ? '#4CAF50' : 
                        portfolioImpactData.overallImpact.status === 'Negative' ? '#F44336' : '#FF9800'
                }}>{portfolioImpactData.overallImpact.status}</span></h3>
                <p style={{ margin: 0, lineHeight: '1.5' }}>
                  {portfolioImpactData.overallImpact.summary}
                </p>
              </div>
            </div>
            
            <h3>Watchlist Impact</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              {portfolioImpactData.watchList.map((item, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px',
                    border: `1px solid ${
                      item.impact.includes('Very Positive') ? '#4CAF50' :
                      item.impact.includes('Positive') ? '#8BC34A' :
                      item.impact.includes('Negative') ? '#F44336' : '#FF9800'
                    }`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{item.symbol} - {item.name}</h3>
                    </div>
                    <div style={{ 
                      color: 
                        item.impact.includes('Very Positive') ? '#4CAF50' :
                        item.impact.includes('Positive') ? '#8BC34A' :
                        item.impact.includes('Negative') ? '#F44336' : '#FF9800',
                      fontWeight: '500'
                    }}>
                      {item.impact}
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>Recent News:</div>
                    <p style={{ margin: 0, fontSize: '0.9rem' }}>{item.recentNews}</p>
                  </div>
                  
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>Recent Events:</div>
                    <p style={{ margin: 0, fontSize: '0.9rem' }}>{item.recentEvents}</p>
                  </div>
                  
                  <div style={{ 
                    backgroundColor: '#1e1e1e',
                    padding: '12px',
                    borderRadius: '4px',
                    borderLeft: '3px solid #4F8BFF'
                  }}>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>AI Recommendation:</div>
                    <p style={{ margin: 0, fontSize: '0.9rem' }}>{item.aiRecommendation}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <h3>Upcoming Events Impact</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {portfolioImpactData.upcomingEvents.map((event, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>{event.event}</h3>
                    <span className={`badge ${
                      event.potentialImpact === 'Very High' || event.potentialImpact === 'High' ? 'danger' :
                      event.potentialImpact === 'Medium' ? 'warning' : 'info'
                    }`}>
                      {event.potentialImpact} Impact
                    </span>
                  </div>
                  
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>Affected Holdings:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {event.affectedHoldings.map((holding, i) => (
                        <span key={i} className="badge info">{holding}</span>
                      ))}
                    </div>
                  </div>
                  
                  <p style={{ margin: '0 0 4px 0', fontSize: '0.9rem' }}>
                    {event.analysis}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="card">
          <h2 className="card-header">Market Sensitivity Analysis</h2>
          <div className="card-content">
            <div style={{ marginBottom: '24px' }}>
              <p style={{ lineHeight: '1.5' }}>
                This analysis identifies key market factors that significantly impact your portfolio based on current holdings and market conditions. Understanding these correlations helps anticipate portfolio behavior during specific market events.
              </p>
            </div>
            
            <h3>Key Correlation Factors</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {portfolioImpactData.correlationAnalysis.map((factor, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>{factor.factor}</h3>
                    <span className={`badge ${
                      factor.riskLevel === 'High' ? 'danger' :
                      factor.riskLevel === 'Medium' ? 'warning' : 'info'
                    }`}>
                      {factor.riskLevel} Risk
                    </span>
                  </div>
                  
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span>Correlation Strength</span>
                      <span style={{ 
                        color: factor.correlation.includes('Strong') ? '#F44336' : 
                               factor.correlation.includes('Moderate') ? '#FF9800' : '#4F8BFF'
                      }}>
                        {factor.correlation}
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className={`progress-bar-fill ${
                          factor.correlation.includes('Strong') ? 'danger' : 
                          factor.correlation.includes('Moderate') ? 'warning' : 'info'
                        }`}
                        style={{ 
                          width: factor.correlation.includes('Strong') ? '90%' : 
                                factor.correlation.includes('Moderate') ? '60%' : '30%'
                        }}
                      />
                    </div>
                  </div>
                  
                  <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem' }}>
                    {factor.explanation}
                  </p>
                  
                  <div style={{ 
                    fontSize: '0.8rem', 
                    backgroundColor: '#1e1e1e',
                    padding: '8px',
                    borderRadius: '4px',
                    color: '#9e9e9e'
                  }}>
                    {factor.correlation.includes('Negative') ? 
                      'When this factor increases, your portfolio tends to decrease in value.' :
                      'When this factor increases, your portfolio tends to increase in value.'
                    }
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
                Generate Detailed Risk Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioImpact;
