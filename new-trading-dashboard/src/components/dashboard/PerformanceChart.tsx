import React, { useState, useEffect } from 'react';
import { portfolioApi } from '../../services/api';

interface PerformanceData {
  months: string[];
  portfolioPerformance: number[];
  benchmarkPerformance: number[];
}

const PerformanceChart: React.FC = () => {
  const [period, setPeriod] = useState<string>('1M');
  const [performanceData, setPerformanceData] = useState<{
    dailyPerformance: number[];
    weeklyPerformance: number[];
    monthlyPerformance: number[];
    yearlyPerformance: number[];
    currentReturn: number;
    dataPeriod: string;
  }>({    
    dailyPerformance: [],
    weeklyPerformance: [],
    monthlyPerformance: [],
    yearlyPerformance: [],
    currentReturn: 0,
    dataPeriod: '1M'
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        setLoading(true);
        
        const portfolioHistory = await portfolioApi.getPerformanceHistory();
        
        if (portfolioHistory && portfolioHistory.daily) {
          setPerformanceData({
            dailyPerformance: portfolioHistory.daily || [],
            weeklyPerformance: portfolioHistory.weekly || [],
            monthlyPerformance: portfolioHistory.monthly || [],
            yearlyPerformance: portfolioHistory.yearly || [],
            currentReturn: portfolioHistory.currentReturn || 0,
            dataPeriod: period
          });
          setError(null);
        } else {
          setPerformanceData({
            dailyPerformance: [2.1, 0.5, -1.3, 0.8, 1.2, -0.3, 1.5, 2.3, 1.8, 0.2, -0.5, 1.7, 2.5, 1.9, 0.1],
            weeklyPerformance: [5.2, 3.8, -2.1, 4.3, 2.7, 1.9, 3.5, 4.8, 2.3, 1.2, -1.5, 3.2],
            monthlyPerformance: [12.5, 8.3, 10.2, 7.5, 9.8, 6.3, 11.2, 13.5, 9.1, 7.8, 10.5, 14.2],
            yearlyPerformance: [67.2, 48.3, 72.5, 53.8, 62.1],
            currentReturn: 14.2,
            dataPeriod: period
          });
        }
      } catch (err) {
        console.error('Error fetching performance data:', err);
        setError('Failed to load performance data');
        
        if (performanceData.dailyPerformance.length === 0) {
          setPerformanceData({
            dailyPerformance: [2.1, 0.5, -1.3, 0.8, 1.2, -0.3, 1.5, 2.3, 1.8, 0.2, -0.5, 1.7, 2.5, 1.9, 0.1],
            weeklyPerformance: [5.2, 3.8, -2.1, 4.3, 2.7, 1.9, 3.5, 4.8, 2.3, 1.2, -1.5, 3.2],
            monthlyPerformance: [12.5, 8.3, 10.2, 7.5, 9.8, 6.3, 11.2, 13.5, 9.1, 7.8, 10.5, 14.2],
            yearlyPerformance: [67.2, 48.3, 72.5, 53.8, 62.1],
            currentReturn: 14.2,
            dataPeriod: period
          });
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchPerformanceData();
    
    setPerformanceData(prev => ({
      ...prev,
      dataPeriod: period
    }));
  }, [period]);

  const getCurrentPerformance = () => {
    switch (period) {
      case '1D':
        return `${performanceData.dailyPerformance.length > 0 ? 
          performanceData.dailyPerformance[performanceData.dailyPerformance.length - 1] : 0}%`;
      case '1W':
        return `${performanceData.weeklyPerformance.length > 0 ? 
          performanceData.weeklyPerformance[performanceData.weeklyPerformance.length - 1] : 0}%`;
      case '1M':
        return `${performanceData.monthlyPerformance.length > 0 ? 
          performanceData.monthlyPerformance[performanceData.monthlyPerformance.length - 1] : 0}%`;
      case '1Y':
        return `${performanceData.yearlyPerformance.length > 0 ? 
          performanceData.yearlyPerformance[performanceData.yearlyPerformance.length - 1] : 0}%`;
      default:
        return `${performanceData.currentReturn}%`;
    }
  };

  const getChartData = () => {
    switch (period) {
      case '1D':
        return performanceData.dailyPerformance.length > 0 ? 
          performanceData.dailyPerformance : [0, 0, 0];
      case '1W':
        return performanceData.weeklyPerformance.length > 0 ? 
          performanceData.weeklyPerformance : [0, 0, 0];
      case '1M':
        return performanceData.monthlyPerformance.length > 0 ? 
          performanceData.monthlyPerformance : [0, 0, 0];
      case '1Y':
        return performanceData.yearlyPerformance.length > 0 ? 
          performanceData.yearlyPerformance : [0, 0, 0];
      default:
        return performanceData.monthlyPerformance.length > 0 ? 
          performanceData.monthlyPerformance : [0, 0, 0];
    }
  };

  const maxValue = Math.max(...getChartData());

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
            <option value="1D">1D</option>
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
            {getChartData().map((value, index) => {
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
                    borderTopRightRadius: index === getChartData().length - 1 ? '4px' : 0,
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
            {getChartData().map((value, index) => {
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
          {getChartData().map((_, index) => (
            <div 
              key={index} 
              style={{ 
                flex: 1, 
                textAlign: 'center', 
                fontSize: '0.75rem', 
                color: '#9e9e9e'
              }}
            >
              {index}
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
