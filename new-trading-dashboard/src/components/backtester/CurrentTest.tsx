import React, { useState, useEffect } from 'react';
import { backtesterApi, BacktestData, TestResults } from '../../services/backtesterApi';

// Interfaces now imported from backtesterApi.ts

const CurrentTest: React.FC = () => {
  const [testData, setTestData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrentTest = async () => {
      try {
        setLoading(true);
        const data = await backtesterApi.getCurrentTest();
        setTestData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching current test:', err);
        setError('Failed to load current test data');
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentTest();
    
    // Refresh data every 30 seconds for live updates
    const intervalId = setInterval(fetchCurrentTest, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  const handleControlAction = async (action: 'pause' | 'resume' | 'cancel') => {
    if (!testData) return;
    
    try {
      const result = await backtesterApi.controlBacktest(action, testData.id);
      if (result.success) {
        // Refresh data after action
        const updatedData = await backtesterApi.getCurrentTest();
        setTestData(updatedData);
      } else {
        setError(result.message);
      }
    } catch (err) {
      console.error(`Error ${action}ing test:`, err);
      setError(`Failed to ${action} test`);
    }
  };

  return (
    <div className="card">
      <h2 className="card-header">Current Backtest</h2>
      <div className="card-content">
        {loading && !testData && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div className="spinner"></div>
            <p>Loading backtest data...</p>
          </div>
        )}
        
        {error && (
          <div style={{ color: '#F44336', padding: '10px', backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: '4px', marginBottom: '10px' }}>
            {error}
          </div>
        )}
        
        {!loading && !testData && !error && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>No active backtest running currently.</p>
            <button style={{ 
              backgroundColor: '#4F8BFF', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '10px'
            }}>
              Start New Backtest
            </button>
          </div>
        )}
        
        {testData && (
        <>
          {/* Progress bar */}
          <div style={{ marginBottom: '12px' }}>
            <div className="progress-bar" style={{ height: '10px', margin: '8px 0' }}>
              <div 
                className="progress-bar-fill info" 
                style={{ width: `${testData.progress}%` }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <small>{testData.progress}% Complete</small>
              <small>ETA: {testData.eta}</small>
            </div>
          </div>

          {/* Test info */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
            <div>
              <strong>Started:</strong> {testData.startedAt}
            </div>
            <div>
              <strong>Elapsed:</strong> {testData.elapsed}
            </div>
            <div>
              <strong>Test Period:</strong> {testData.testPeriod}
            </div>
          </div>

          <div style={{ marginBottom: '8px' }}>
            <strong>Symbols:</strong> {testData.symbols.join(', ')}
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <strong>Current Stage:</strong> <span style={{ color: '#4F8BFF' }}>{testData.executionStage}</span>
          </div>

        {/* Results section */}
        {testData.results && (
          <>
            <h4>Initial Results</h4>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>
                  {testData.results.winRate}%
                </div>
                <div style={{ fontSize: '12px', color: '#787878' }}>
                  Win Rate
                </div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>
                  {testData.results.profitFactor}
                </div>
                <div style={{ fontSize: '12px', color: '#787878' }}>
                  Profit Factor
                </div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>
                  {testData.results.sharpeRatio}
                </div>
                <div style={{ fontSize: '12px', color: '#787878' }}>
                  Sharpe Ratio
                </div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF5252' }}>
                  {testData.results.maxDrawdown}%
                </div>
                <div style={{ fontSize: '12px', color: '#787878' }}>
                  Max Drawdown
                </div>
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginTop: '20px' }}>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{testData.results.totalTrades}</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Total Trades</div>
              </div>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#4CAF50' }}>{testData.results.expectancy.toFixed(2)}</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Expectancy</div>
              </div>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: testData.results.annualizedReturn > 0 ? '#4CAF50' : '#F44336' }}>
                  {testData.results.annualizedReturn}%
                </div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Annual Return</div>
              </div>
            </div>
          </>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
          <button 
            style={{ 
              backgroundColor: '#F44336', 
              color: 'white', 
              border: 'none', 
              padding: '6px 12px', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
            onClick={() => handleControlAction('cancel')}
          >
            Cancel Test
          </button>
          
          {testData.status === 'running' ? (
            <button 
              style={{ 
                backgroundColor: '#FF9800', 
                color: 'white', 
                border: 'none', 
                padding: '6px 12px', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              onClick={() => handleControlAction('pause')}
            >
              Pause Test
            </button>
          ) : testData.status === 'paused' ? (
            <button 
              style={{ 
                backgroundColor: '#4CAF50', 
                color: 'white', 
                border: 'none', 
                padding: '6px 12px', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              onClick={() => handleControlAction('resume')}
            >
              Resume Test
            </button>
          ) : null}
          
          {/* Deploy button appears only for completed backtests with good results */}
          {testData.status === 'completed' && testData.results && testData.results.profitFactor > 1.5 && (
            <button 
              style={{ 
                backgroundColor: '#4F8BFF', 
                color: 'white', 
                border: 'none', 
                padding: '6px 12px', 
                borderRadius: '4px',
                cursor: 'pointer',
                marginLeft: '12px'
              }}
              onClick={() => {
                // This would open a deployment confirmation modal in a real implementation
                alert('Deployment would require approval before going live');
              }}
            >
              Request Deployment
            </button>
          )}
        </div>
        </>
        )}
      </div>
    </div>
  );
};

export default CurrentTest;
