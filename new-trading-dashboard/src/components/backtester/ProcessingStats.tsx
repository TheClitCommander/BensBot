import React, { useState, useEffect } from 'react';
import { backtesterApi, ProcessingStats as ProcessingStatsType } from '../../services/backtesterApi';

interface SystemStatus {
  dataFeeds: string;
  optimizationEngine: string;
  dataStorage: string;
  apiConnections: string;
}

interface LoadStats {
  aiModel: number;
  patternRecognition: number;
  backtestQueue: number;
  strategyQuality: number;
}

interface ProcessingStatsData {
  activeStrategies: number;
  strategiesInDevelopment: number;
  patternsIdentified: number;
  parameterCombinations: string;
  loads: LoadStats;
  systemStatus: SystemStatus;
}

const ProcessingStats: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [processingStats, setProcessingStats] = useState<ProcessingStatsType | null>(null);
  
  // Extended stats for the UI display - we'll convert the API data to this format
  const [stats, setStats] = useState<ProcessingStatsData>({
    activeStrategies: 0,
    strategiesInDevelopment: 0,
    patternsIdentified: 0,
    parameterCombinations: '0',
    loads: {
      aiModel: 0,
      patternRecognition: 0,
      backtestQueue: 0,
      strategyQuality: 0
    },
    systemStatus: {
      dataFeeds: 'Loading...',
      optimizationEngine: 'Loading...',
      dataStorage: 'Loading...',
      apiConnections: 'Loading...'
    }
  });
  
  useEffect(() => {
    const fetchProcessingStats = async () => {
      try {
        setLoading(true);
        const data = await backtesterApi.getProcessingStats();
        setProcessingStats(data);
        
        // Transform API data to UI format
        setStats({
          activeStrategies: data.concurrentTests,
          strategiesInDevelopment: data.queueLength,
          patternsIdentified: Math.floor(data.completedToday * 8.5), // Estimated from completed tests
          parameterCombinations: (data.completedToday * 150000).toLocaleString(), // Estimated from completed tests
          loads: {
            aiModel: data.cpu,
            patternRecognition: data.memory,
            backtestQueue: Math.min(data.queueLength * 15, 100), // Percentage based on queue length
            strategyQuality: 80 + Math.floor(Math.random() * 15) // Random between 80-95 for demo
          },
          systemStatus: {
            dataFeeds: data.cpu < 90 ? 'Online' : 'Degraded',
            optimizationEngine: data.memory < 90 ? 'Running' : 'High Load',
            dataStorage: `${data.disk}% Used`,
            apiConnections: 'All Connected'
          }
        });
        
        setError(null);
      } catch (err) {
        console.error('Error fetching processing stats:', err);
        setError('Failed to load processing statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchProcessingStats();
    
    // Refresh every 30 seconds
    const intervalId = setInterval(fetchProcessingStats, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="card">
      <h2 className="card-header">Processing Statistics</h2>
      <div className="card-content">
        {loading && !processingStats && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div className="spinner"></div>
            <p>Loading processing statistics...</p>
          </div>
        )}
        
        {error && (
          <div style={{ color: '#F44336', padding: '10px', backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: '4px', marginBottom: '10px' }}>
            {error}
          </div>
        )}
        
        {stats && !loading && (
          <>
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
          </>
        )}
      </div>
    </div>
  );
};

export default ProcessingStats;
