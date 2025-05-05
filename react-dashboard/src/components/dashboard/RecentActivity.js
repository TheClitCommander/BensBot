import React from 'react';

const RecentActivity = () => {
  // Mock data - would be connected to your trading engine
  const activityData = [
    {
      id: 'ACT-001',
      type: 'TRADE',
      title: 'Buy Order Executed',
      description: 'Bought 50 shares of AAPL at $198.45',
      timestamp: '2025-05-04T13:45:21',
      strategy: 'Tech Momentum'
    },
    {
      id: 'ACT-002',
      type: 'ALERT',
      title: 'Strategy Signal',
      description: 'New buy signal generated for BTC-USD',
      timestamp: '2025-05-04T12:32:10',
      strategy: 'BTC Volatility Edge'
    },
    {
      id: 'ACT-003',
      type: 'SYSTEM',
      title: 'Strategy Optimization',
      description: 'Forex Range Trader parameters updated',
      timestamp: '2025-05-04T11:15:42',
      strategy: 'Forex Range Trader'
    },
    {
      id: 'ACT-004',
      type: 'TRADE',
      title: 'Sell Order Executed',
      description: 'Sold 25 shares of MSFT at $415.30',
      timestamp: '2025-05-04T10:05:38',
      strategy: 'Tech Momentum'
    },
    {
      id: 'ACT-005',
      type: 'ALERT',
      title: 'Risk Warning',
      description: 'Portfolio Beta exceeding target threshold',
      timestamp: '2025-05-04T09:30:15',
      strategy: 'Risk Manager'
    }
  ];

  // Function to get appropriate icon and color based on activity type
  const getActivityStyles = (type) => {
    switch (type) {
      case 'TRADE':
        return { icon: 'swap_horiz', color: '#4F8BFF' };
      case 'ALERT':
        return { icon: 'warning', color: '#FF9800' };
      case 'SYSTEM':
        return { icon: 'settings', color: '#9E9E9E' };
      default:
        return { icon: 'info', color: '#4CAF50' };
    }
  };

  // Format timestamp to readable format
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="card">
      <h2 className="card-header">Recent Activity</h2>
      <div className="card-content">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {activityData.map((activity) => {
            const styles = getActivityStyles(activity.type);
            
            return (
              <div 
                key={activity.id} 
                className="activity-item"
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div 
                    style={{ 
                      backgroundColor: `${styles.color}20`, 
                      color: styles.color,
                      padding: '8px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <span className="material-icons" style={{ fontSize: '18px' }}>{styles.icon}</span>
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h3 className="activity-title">{activity.title}</h3>
                      <span className="activity-time">{formatTime(activity.timestamp)}</span>
                    </div>
                    <p className="activity-desc">{activity.description}</p>
                    {activity.strategy && (
                      <div style={{ fontSize: '0.75rem', color: '#9e9e9e', marginTop: '4px' }}>
                        Strategy: {activity.strategy}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default RecentActivity;
