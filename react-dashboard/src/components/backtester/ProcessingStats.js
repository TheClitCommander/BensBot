import React from 'react';

const ProcessingStats = () => {
  // Mock data
  const stats = {
    activeStrategies: 7,
    strategiesInDevelopment: 24,
    patternsIdentified: 142,
    parameterCombinations: '3.2M',
    loads: {
      aiModel: 78,
      patternRecognition: 89,
      backtestQueue: 45,
      strategyQuality: 92
    },
    systemStatus: {
      dataFeeds: 'Online',
      optimizationEngine: 'Running',
      dataStorage: '64% Used',
      apiConnections: 'All Connected'
    }
  };

  return (
    <div className="card">
      <h2 className="card-header">Processing Statistics</h2>
      <div className="card-content">
        {/* Processing statistics */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.activeStrategies}</div>
            <div style={{ fontSize: '14px', color: '#787878' }}>Active Strategies</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.strategiesInDevelopment}</div>
            <div style={{ fontSize: '14px', color: '#787878' }}>Strategies in Development</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.patternsIdentified}</div>
            <div style={{ fontSize: '14px', color: '#787878' }}>Patterns Identified</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.parameterCombinations}</div>
            <div style={{ fontSize: '14px', color: '#787878' }}>Parameter Combinations</div>
          </div>
        </div>

        {/* Progress bars */}
        <div style={{ marginTop: '24px' }}>
          {/* AI Model Load */}
          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <strong>AI Model Load:</strong>
              <span>{stats.loads.aiModel}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-bar-fill success" 
                style={{ width: `${stats.loads.aiModel}%` }}
              />
            </div>
          </div>

          {/* Pattern Recognition */}
          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <strong>Pattern Recognition:</strong>
              <span>{stats.loads.patternRecognition}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-bar-fill success" 
                style={{ width: `${stats.loads.patternRecognition}%` }}
              />
            </div>
          </div>

          {/* Backtest Queue */}
          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <strong>Backtest Queue:</strong>
              <span>{stats.loads.backtestQueue}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-bar-fill warning" 
                style={{ width: `${stats.loads.backtestQueue}%` }}
              />
            </div>
          </div>

          {/* Strategy Quality */}
          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <strong>Strategy Quality:</strong>
              <span>{stats.loads.strategyQuality}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-bar-fill success" 
                style={{ width: `${stats.loads.strategyQuality}%` }}
              />
            </div>
          </div>
        </div>

        {/* System Status */}
        <div style={{ marginTop: '24px' }}>
          <h4 style={{ marginBottom: '12px' }}>System Status</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {Object.entries(stats.systemStatus).map(([key, value]) => (
              <div 
                key={key} 
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  backgroundColor: '#272727',
                  borderRadius: '4px'
                }}
              >
                <div style={{ fontWeight: '500' }}>
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </div>
                <div style={{ 
                  color: 
                    value.includes('Online') || value.includes('Running') || value.includes('Connected') 
                      ? '#4CAF50' 
                      : value.includes('Error') || value.includes('Offline') 
                        ? '#F44336' 
                        : '#FF9800' 
                }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingStats;
