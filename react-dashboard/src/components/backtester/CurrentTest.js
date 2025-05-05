import React from 'react';

const CurrentTest = () => {
  // This data is based on the HTML you shared
  const testData = {
    progress: 68,
    eta: '2025-05-04 14:30:00',
    startedAt: '2025-05-04 12:15:32',
    elapsed: '01:30:15',
    testPeriod: '2020-01-01 to 2025-05-01',
    symbols: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'],
    results: {
      winRate: 56.4,
      profitFactor: 1.82,
      sharpeRatio: 1.45,
      maxDrawdown: 12.3
    }
  };

  return (
    <div className="card">
      <h2 className="card-header">Current Backtest</h2>
      <div className="card-content">
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

        <div style={{ marginBottom: '16px' }}>
          <strong>Symbols:</strong> {testData.symbols.join(', ')}
        </div>

        {/* Results section */}
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

        {/* Action buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
          <button style={{ 
            backgroundColor: '#F44336', 
            color: 'white', 
            border: 'none', 
            padding: '6px 12px', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            Cancel Test
          </button>
          <button style={{ 
            backgroundColor: '#FF9800', 
            color: 'white', 
            border: 'none', 
            padding: '6px 12px', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            Pause Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default CurrentTest;
