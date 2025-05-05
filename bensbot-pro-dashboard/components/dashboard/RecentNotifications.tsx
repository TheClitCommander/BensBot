import { useState } from 'react';
import { Bell, AlertTriangle, Settings, XCircle, DollarSign } from 'lucide-react';

// Sample data - this would be fetched from MongoDB in production
const notifications = [
  { id: 1, type: 'trade', message: 'New Trade: Bought AAPL at $182.45 (Momentum Strategy)', time: '09:45 AM' },
  { id: 2, type: 'alert', message: 'Market Regime: Bullish sentiment detected in Technology sector', time: '09:30 AM' },
  { id: 3, type: 'system', message: 'Daily allocation updated: +5% to Momentum, -5% from Option Spreads', time: '09:15 AM' },
  { id: 4, type: 'error', message: 'API Error: Unable to fetch data for symbol XYZ', time: '08:50 AM' },
  { id: 5, type: 'trade', message: 'Trade Closed: Sold MSFT at $415.30, +3.1% profit', time: 'Yesterday' },
];

export default function RecentNotifications() {
  return (
    <div className="dashboard-card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="card-title">Recent Notifications</h2>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Last updated: {new Date().toLocaleTimeString()}
        </span>
      </div>
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {notifications.map(notification => (
          <div 
            key={notification.id} 
            className="flex items-start p-2 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded"
          >
            {notification.type === 'trade' && 
              <DollarSign className="h-5 w-5 text-blue-500 mr-2 mt-0.5" />}
            
            {notification.type === 'alert' && 
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2 mt-0.5" />}
            
            {notification.type === 'system' && 
              <Settings className="h-5 w-5 text-gray-500 dark:text-gray-400 mr-2 mt-0.5" />}
            
            {notification.type === 'error' && 
              <XCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5" />}
            
            <div className="flex-1">
              <p className="text-sm text-gray-700 dark:text-gray-200">{notification.message}</p>
              <span className="text-xs text-gray-500 dark:text-gray-400">{notification.time}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 text-right">
        <button className="text-blue-500 dark:text-[var(--accent-color)] text-sm hover:underline">
          View all notifications
        </button>
      </div>
    </div>
  );
}
