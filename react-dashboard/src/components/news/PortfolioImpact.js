import React from 'react';

const PortfolioImpact = () => {
  // Mock data for portfolio impact analysis
  const portfolioImpactData = {
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
                                   portfolioImpactData.overallImpact.score >= 50 ? '#FF980020' : 
                                   '#F4433620',
                  borderRadius: '50%',
                  width: '80px',
                  height: '80px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: portfolioImpactData.overallImpact.score >= 70 ? '#4CAF50' : 
                         portfolioImpactData.overallImpact.score >= 50 ? '#FF9800' : 
                         '#F44336',
                  border: `2px solid ${
                    portfolioImpactData.overallImpact.score >= 70 ? '#4CAF50' : 
                    portfolioImpactData.overallImpact.score >= 50 ? '#FF9800' : 
                    '#F44336'
                  }`
                }}
              >
                {portfolioImpactData.overallImpact.score}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ 
                  color: portfolioImpactData.overallImpact.score >= 70 ? '#4CAF50' : 
                         portfolioImpactData.overallImpact.score >= 50 ? '#FF9800' : 
                         '#F44336',
                  fontWeight: 'bold',
                  fontSize: '1.1rem',
                  marginBottom: '8px'
                }}>
                  {portfolioImpactData.overallImpact.status} Overall Impact
                </div>
                <p style={{ margin: 0, lineHeight: '1.5' }}>
                  {portfolioImpactData.overallImpact.summary}
                </p>
              </div>
            </div>
            
            <h3>Assets to Watch</h3>
            <div className="table-container" style={{ marginBottom: '24px' }}>
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Impact</th>
                    <th>Recent Development</th>
                    <th>AI Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolioImpactData.watchList.map((asset) => (
                    <tr key={asset.symbol}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 500 }}>{asset.symbol}</span>
                          <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>{asset.name}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${
                          asset.impact.includes('Positive') ? 'success' :
                          asset.impact.includes('Negative') ? 'danger' : 'info'
                        }`}>
                          {asset.impact}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.9rem' }}>
                          {asset.recentNews}
                        </div>
                      </td>
                      <td>
                        <div style={{ 
                          fontSize: '0.9rem',
                          padding: '8px',
                          backgroundColor: '#1e1e1e',
                          borderRadius: '4px',
                          borderLeft: `3px solid ${
                            asset.impact.includes('Positive') ? '#4CAF50' :
                            asset.impact.includes('Negative') ? '#F44336' : '#4F8BFF'
                          }`
                        }}>
                          {asset.aiRecommendation}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <h3>Upcoming Catalysts</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              {portfolioImpactData.upcomingEvents.map((event, index) => (
                <div 
                  key={index}
                  style={{ 
                    padding: '16px', 
                    backgroundColor: '#272727', 
                    borderRadius: '8px',
                    display: 'flex',
                    gap: '16px'
                  }}
                >
                  <div 
                    style={{ 
                      minWidth: '80px',
                      textAlign: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center',
                      backgroundColor: '#1e1e1e',
                      padding: '12px',
                      borderRadius: '8px'
                    }}
                  >
                    <div className={`badge ${
                      event.potentialImpact === 'Very High' || event.potentialImpact === 'High' ? 'danger' :
                      event.potentialImpact === 'Medium' ? 'warning' : 'info'
                    }`} style={{ marginBottom: '8px' }}>
                      {event.potentialImpact}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Impact</div>
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1rem' }}>{event.event}</h3>
                    <div style={{ fontSize: '0.9rem', marginBottom: '12px' }}>
                      {event.analysis}
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {event.affectedHoldings.map((symbol, i) => (
                        <div key={i} className="badge info">{symbol}</div>
                      ))}
                    </div>
                  </div>
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
