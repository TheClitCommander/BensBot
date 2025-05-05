import React, { useState, useEffect } from 'react';
import { backtesterApi, BacktestStrategy } from '../../services/backtesterApi';

// BacktestStrategy is now imported from backtesterApi.ts

const StrategyQueue: React.FC = () => {
  const [strategyQueue, setStrategyQueue] = useState<BacktestStrategy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  
  useEffect(() => {
    const fetchStrategyQueue = async () => {
      try {
        setLoading(true);
        const data = await backtesterApi.getStrategyQueue();
        setStrategyQueue(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching strategy queue:', err);
        setError('Failed to load strategy queue');
      } finally {
        setLoading(false);
      }
    };

    fetchStrategyQueue();
    
    // Refresh data every minute
    const intervalId = setInterval(fetchStrategyQueue, 60000);
    
    return () => clearInterval(intervalId);
  }, []);
  
  // Filter strategies based on priority
  const filteredStrategies = strategyQueue.filter(strategy => {
    if (priorityFilter === 'all') return true;
    return strategy.priority.toLowerCase() === priorityFilter.toLowerCase();
  });

  // Get badge color based on priority
  const getPriorityBadgeColor = (priority: 'High' | 'Medium' | 'Low'): string => {
    switch (priority) {
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

  const handleSubmitNewStrategy = () => {
    // In a real implementation, this would open a modal or redirect to a strategy creation form
    alert('This would open a form to submit a new strategy for backtesting');
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Strategy Queue</h2>
        <select 
          style={{ 
            backgroundColor: '#333', 
            color: 'white', 
            border: 'none', 
            padding: '5px 10px',
            borderRadius: '4px'
          }}
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
        >
          <option value="all">All Priorities</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
      </div>
      
      <div className="card-content">
        {loading && strategyQueue.length === 0 && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div className="spinner"></div>
            <p>Loading strategy queue...</p>
          </div>
        )}
        
        {error && (
          <div style={{ color: '#F44336', padding: '10px', backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: '4px', marginBottom: '10px' }}>
            {error}
          </div>
        )}
        
        {!loading && strategyQueue.length === 0 && !error && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>No strategies in queue.</p>
          </div>
        )}
        {strategyQueue.length > 0 && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Priority</th>
                  <th>Est. Start Time</th>
                  <th>Complexity</th>
                </tr>
              </thead>
              <tbody>
                {filteredStrategies.map((strategy) => (
                <tr key={strategy.id}>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 500 }}>{strategy.name}</span>
                      <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>
                        {strategy.assets.slice(0, 3).join(', ')}
                        {strategy.assets.length > 3 ? `, +${strategy.assets.length - 3} more` : ''}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${getPriorityBadgeColor(strategy.priority)}`}>
                      {strategy.priority}
                    </span>
                  </td>
                  <td>
                    {new Date(strategy.estimatedStart).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td>{strategy.complexity}</td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
          <span style={{ fontSize: '0.875rem', color: '#9e9e9e' }}>
            {priorityFilter === 'all' ? strategyQueue.length : filteredStrategies.length} strategies in queue
            {priorityFilter !== 'all' && ` (${priorityFilter} priority)`}
          </span>
          <div>
            <button 
              style={{ 
                backgroundColor: '#4F8BFF', 
                color: 'white', 
                border: 'none', 
                padding: '6px 12px', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              onClick={handleSubmitNewStrategy}
            >
              Submit New Strategy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyQueue;
