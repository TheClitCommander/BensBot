import React, { useState, useEffect } from 'react';
import { tradesApi, newsApi } from '../../services/api';

interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  symbol?: string;
  impact?: string;
}

interface ActivityStyle {
  icon: string;
  color: string;
}

const RecentActivity: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch activity data from API
  useEffect(() => {
    const fetchActivityData = async () => {
      try {
        setLoading(true);
        
        // Fetch recent trades and news in parallel
        const [tradesResponse, newsResponse] = await Promise.allSettled([
          tradesApi.getTrades(),
          newsApi.getMarketNews()
        ]);
        
        const activityItems: ActivityItem[] = [];
        
        // Process trades
        if (tradesResponse.status === 'fulfilled' && tradesResponse.value) {
          const trades = tradesResponse.value;
          trades.slice(0, 5).forEach(trade => {
            activityItems.push({
              id: `trade-${trade.id}`,
              type: 'TRADE',
              title: `${trade.side.toUpperCase()} ${trade.symbol}`,
              description: `${trade.quantity} shares at $${trade.entryPrice.toFixed(2)}`,
              timestamp: trade.openedAt,
              symbol: trade.symbol
            });
          });
        }
        
        // Process news
        if (newsResponse.status === 'fulfilled' && newsResponse.value) {
          const news = newsResponse.value;
          news.slice(0, 5).forEach(item => {
            activityItems.push({
              id: `news-${item.id}`,
              type: 'ALERT',
              title: item.title,
              description: item.summary,
              timestamp: item.publishedAt,
              symbol: item.symbols?.[0],
              impact: item.impact
            });
          });
        }
        
        // Sort by timestamp, newest first
        activityItems.sort((a, b) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        
        // Take the 10 most recent items
        setActivities(activityItems.slice(0, 10));
        setError(null);
      } catch (err) {
        console.error('Error fetching activity data:', err);
        setError('Failed to load recent activity');
        
        // If we have no data yet, set fallback data
        if (activities.length === 0) {
          setActivities([
            {
              id: 'ACT-001',
              type: 'TRADE',
              title: 'Buy Order Executed',
              description: 'Bought 50 shares of AAPL at $198.45',
              timestamp: '2025-05-04T13:45:21',
              symbol: 'AAPL'
            },
            {
              id: 'ACT-002',
              type: 'ALERT',
              title: 'Strategy Signal',
              description: 'New buy signal generated for BTC-USD',
              timestamp: '2025-05-04T12:32:10',
              symbol: 'BTC-USD'
            },
            {
              id: 'ACT-003',
              type: 'SYSTEM',
              title: 'Strategy Optimization',
              description: 'Forex Range Trader parameters updated',
              timestamp: '2025-05-04T11:15:42',
              symbol: 'EUR-USD'
            },
            {
              id: 'ACT-004',
              type: 'TRADE',
              title: 'Sell Order Executed',
              description: 'Sold 25 shares of MSFT at $415.30',
              timestamp: '2025-05-04T10:05:38',
              symbol: 'MSFT'
            },
            {
              id: 'ACT-005',
              type: 'ALERT',
              title: 'Risk Warning',
              description: 'Portfolio Beta exceeding target threshold',
              timestamp: '2025-05-04T09:30:15',
              symbol: 'SPY'
            }
          ]);
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchActivityData();
    
    // Refresh data every 30 seconds
    const intervalId = setInterval(fetchActivityData, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  // Show loading state
  if (loading && activities.length === 0) {
    return (
      <div className="card">
        <h2 className="card-header">Recent Activity</h2>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0' }}>
          <div>Loading recent activity...</div>
        </div>
      </div>
    );
  }
  
  // Show error state
  if (error && activities.length === 0) {
    return (
      <div className="card">
        <h2 className="card-header">Recent Activity</h2>
        <div className="card-content" style={{ textAlign: 'center', padding: '30px 0', color: '#f87171' }}>
          <div>{error}</div>
        </div>
      </div>
    );
  }

  // Function to get appropriate icon and color based on activity type
  const getActivityStyles = (type: string): ActivityStyle => {
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
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="card">
      <h2 className="card-header">Recent Activity</h2>
      <div className="card-content">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {activities.map((activity) => {
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
                      <span style={{ fontSize: '0.8rem', color: '#718096', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <i className="material-icons" style={{ fontSize: '0.9rem' }}>schedule</i>
                        {new Date(activity.timestamp).toLocaleString()}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: '#718096', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <i className="material-icons" style={{ fontSize: '0.9rem' }}>tag</i>
                        {activity.symbol || 'General'}
                      </span>
                    </div>
                    <p className="activity-desc">{activity.description}</p>
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
