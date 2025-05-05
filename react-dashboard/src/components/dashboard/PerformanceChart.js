import React from 'react';

const PerformanceChart = () => {
  // This component would normally use a charting library like Chart.js or Recharts
  // For now, I'll create a simple visualized chart using CSS

  // Mock data - would be connected to your trading engine
  const performanceData = {
    months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    portfolioPerformance: [0, 2.3, 5.1, 3.8, 7.4, 6.2, 9.5, 11.2, 15.8, 14.1, 18.2, 21.5],
    benchmarkPerformance: [0, 1.2, 3.5, 2.7, 5.1, 4.3, 6.7, 7.9, 9.4, 8.5, 10.2, 12.1]
  };

  // Calculate the maximum value for scaling
  const maxValue = Math.max(
    ...performanceData.portfolioPerformance,
    ...performanceData.benchmarkPerformance
  );

  return (
    <div className="card">
      <div className="card-header">
        <h2>Performance</h2>
        <div>
          <select 
            style={{ 
              backgroundColor: '#333', 
              color: 'white', 
              border: 'none', 
              padding: '5px 10px',
              borderRadius: '4px'
            }}
          >
            <option value="1Y">1Y</option>
            <option value="6M">6M</option>
            <option value="3M">3M</option>
            <option value="1M">1M</option>
            <option value="1W">1W</option>
          </select>
        </div>
      </div>
      
      <div className="card-content">
        <div style={{ display: 'flex', marginBottom: '10px', gap: '15px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#4F8BFF', borderRadius: '2px' }} />
            <span style={{ fontSize: '0.875rem' }}>Portfolio</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#9E9E9E', borderRadius: '2px' }} />
            <span style={{ fontSize: '0.875rem' }}>S&P 500</span>
          </div>
        </div>
        
        {/* Chart visualization */}
        <div style={{ position: 'relative', height: '200px', marginBottom: '20px' }}>
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((percent) => (
            <div 
              key={percent}
              style={{
                position: 'absolute',
                bottom: `${percent}%`,
                left: 0,
                right: 0,
                borderBottom: percent === 0 ? '2px solid #333' : '1px dashed #333',
                zIndex: 1
              }}
            />
          ))}
          
          {/* Portfolio performance line */}
          <div style={{ 
            position: 'absolute', 
            bottom: 0, 
            left: 0, 
            right: 0, 
            height: '100%', 
            display: 'flex', 
            alignItems: 'flex-end',
            zIndex: 2
          }}>
            {performanceData.portfolioPerformance.map((value, index) => {
              const heightPercent = (value / maxValue) * 100;
              return (
                <div 
                  key={`portfolio-${index}`}
                  style={{ 
                    flex: 1,
                    height: `${heightPercent}%`,
                    backgroundColor: 'rgba(79, 139, 255, 0.2)',
                    position: 'relative',
                    borderTopLeftRadius: index === 0 ? '4px' : 0,
                    borderTopRightRadius: index === performanceData.portfolioPerformance.length - 1 ? '4px' : 0,
                  }}
                >
                  <div 
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '3px',
                      backgroundColor: '#4F8BFF',
                      borderRadius: '2px'
                    }}
                  />
                </div>
              );
            })}
          </div>
          
          {/* Benchmark performance line */}
          <div style={{ 
            position: 'absolute', 
            bottom: 0, 
            left: 0, 
            right: 0, 
            height: '100%', 
            display: 'flex', 
            alignItems: 'flex-end',
            zIndex: 3
          }}>
            {performanceData.benchmarkPerformance.map((value, index) => {
              const heightPercent = (value / maxValue) * 100;
              return (
                <div 
                  key={`benchmark-${index}`}
                  style={{ 
                    flex: 1,
                    height: `${heightPercent}%`,
                    position: 'relative',
                  }}
                >
                  <div 
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '3px',
                      backgroundColor: '#9E9E9E',
                      borderRadius: '2px'
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
        
        {/* X-axis labels */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {performanceData.months.map((month, index) => (
            <div 
              key={index} 
              style={{ 
                flex: 1, 
                textAlign: 'center', 
                fontSize: '0.75rem', 
                color: '#9e9e9e'
              }}
            >
              {month}
            </div>
          ))}
        </div>
        
        {/* Summary stats */}
        <div style={{ display: 'flex', marginTop: '1.5rem', gap: '1.5rem' }}>
          <div className="stat-item">
            <div className="stat-value positive-value">+21.5%</div>
            <div className="stat-label">YTD Return</div>
          </div>
          <div className="stat-item">
            <div className="stat-value positive-value">+9.4%</div>
            <div className="stat-label">Outperformance</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">1.45</div>
            <div className="stat-label">Sharpe Ratio</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;
