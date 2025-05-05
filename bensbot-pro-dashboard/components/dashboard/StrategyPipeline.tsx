import { useState } from 'react';
import { RefreshCw, ArrowRight } from 'lucide-react';

// Sample data - this would be fetched from MongoDB in production
const backtestedStrategies = [
  { 
    name: 'Momentum', 
    status: 'Passed', 
    metrics: { return: 12.5, maxDrawdown: 8.2, sharpe: 1.8, winRate: 65 },
    readyForPaper: true
  },
  { 
    name: 'Mean Reversion', 
    status: 'Passed', 
    metrics: { return: 9.8, maxDrawdown: 7.5, sharpe: 1.5, winRate: 62 },
    readyForPaper: true
  },
  { 
    name: 'Trend Following', 
    status: 'In Progress', 
    metrics: { return: 0, maxDrawdown: 0, sharpe: 0, winRate: 0 },
    readyForPaper: false
  },
  { 
    name: 'Breakout Swing', 
    status: 'Failed', 
    metrics: { return: 4.2, maxDrawdown: 12.8, sharpe: 0.9, winRate: 48 },
    readyForPaper: false
  },
  { 
    name: 'Volatility Breakout', 
    status: 'Passed', 
    metrics: { return: 14.2, maxDrawdown: 10.2, sharpe: 1.7, winRate: 58 },
    readyForPaper: true
  },
  { 
    name: 'Option Spreads', 
    status: 'Not Started', 
    metrics: { return: 0, maxDrawdown: 0, sharpe: 0, winRate: 0 },
    readyForPaper: false
  },
];

const paperStrategies = [
  { 
    name: 'Momentum', 
    status: 'Running', 
    metrics: { return: 8.5, maxDrawdown: 5.1, sharpe: 1.6, winRate: 60 },
    readyForLive: true
  },
  { 
    name: 'Mean Reversion', 
    status: 'Running', 
    metrics: { return: 6.2, maxDrawdown: 4.8, sharpe: 1.3, winRate: 58 },
    readyForLive: true
  },
  { 
    name: 'Volatility Breakout', 
    status: 'Not Started', 
    metrics: { return: 0, maxDrawdown: 0, sharpe: 0, winRate: 0 },
    readyForLive: false
  },
];

const liveStrategies = [
  { 
    name: 'Momentum', 
    status: 'Active', 
    metrics: { return: 3.2, maxDrawdown: 1.8, sharpe: 1.4, winRate: 62 },
  },
];

export default function StrategyPipeline() {
  const [activeTab, setActiveTab] = useState('backtest');
  
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'Passed':
      case 'Active':
      case 'Running':
        return 'text-green-500 dark:text-[var(--success-color)]';
      case 'Failed':
        return 'text-red-500 dark:text-[var(--danger-color)]';
      case 'In Progress':
        return 'text-blue-500 dark:text-[var(--accent-color)]';
      default:
        return 'text-gray-500 dark:text-gray-400';
    }
  };
  
  return (
    <div className="dashboard-card">
      <div className="mb-6">
        <div className="flex border-b border-gray-200 dark:border-[var(--border-color)]">
          <button 
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'backtest' 
              ? 'border-b-2 border-blue-500 dark:border-[var(--accent-color)] text-blue-600 dark:text-[var(--accent-color)]' 
              : 'text-gray-500 dark:text-gray-400'}`}
            onClick={() => setActiveTab('backtest')}
          >
            1. Backtest
          </button>
          <button 
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'paper' 
              ? 'border-b-2 border-blue-500 dark:border-[var(--accent-color)] text-blue-600 dark:text-[var(--accent-color)]' 
              : 'text-gray-500 dark:text-gray-400'}`}
            onClick={() => setActiveTab('paper')}
          >
            2. Paper Trading
          </button>
          <button 
            className={`px-4 py-2 font-medium text-sm ${activeTab === 'live' 
              ? 'border-b-2 border-blue-500 dark:border-[var(--accent-color)] text-blue-600 dark:text-[var(--accent-color)]' 
              : 'text-gray-500 dark:text-gray-400'}`}
            onClick={() => setActiveTab('live')}
          >
            3. Live Trading
          </button>
        </div>
      </div>
      
      {activeTab === 'backtest' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Backtest Strategies</h2>
            <button className="bg-blue-500 dark:bg-[var(--accent-color)] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 flex items-center">
              <RefreshCw className="w-4 h-4 mr-2" />
              Run New Backtest
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-[var(--card-bg)]">
              <thead className="bg-gray-50 dark:bg-[var(--sidebar-bg)]">
                <tr>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Return</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Max Drawdown</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sharpe</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Win Rate</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-[var(--border-color)]">
                {backtestedStrategies.map((strategy, idx) => (
                  <tr key={idx}>
                    <td className="py-4 px-4 text-sm font-medium text-gray-900 dark:text-white">{strategy.name}</td>
                    <td className={`py-4 px-4 text-sm ${getStatusColor(strategy.status)}`}>{strategy.status}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.return > 0 ? `${strategy.metrics.return}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.maxDrawdown > 0 ? `${strategy.metrics.maxDrawdown}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.sharpe > 0 ? strategy.metrics.sharpe.toFixed(2) : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.winRate > 0 ? `${strategy.metrics.winRate}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm">
                      {strategy.readyForPaper ? (
                        <button 
                          className="bg-green-500 dark:bg-[var(--success-color)] text-white px-3 py-1 rounded text-xs hover:bg-green-600 flex items-center"
                          onClick={() => setActiveTab('paper')}
                        >
                          Promote to Paper <ArrowRight className="w-3 h-3 ml-1" />
                        </button>
                      ) : (
                        <button 
                          className="bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded text-xs cursor-not-allowed"
                          disabled
                        >
                          Not Ready
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {activeTab === 'paper' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Paper Trading Strategies</h2>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Running with simulated money to validate performance
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-[var(--card-bg)]">
              <thead className="bg-gray-50 dark:bg-[var(--sidebar-bg)]">
                <tr>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Return</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Max Drawdown</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sharpe</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Win Rate</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-[var(--border-color)]">
                {paperStrategies.map((strategy, idx) => (
                  <tr key={idx}>
                    <td className="py-4 px-4 text-sm font-medium text-gray-900 dark:text-white">{strategy.name}</td>
                    <td className={`py-4 px-4 text-sm ${getStatusColor(strategy.status)}`}>{strategy.status}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.return > 0 ? `${strategy.metrics.return}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.maxDrawdown > 0 ? `${strategy.metrics.maxDrawdown}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.sharpe > 0 ? strategy.metrics.sharpe.toFixed(2) : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.winRate > 0 ? `${strategy.metrics.winRate}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm">
                      {strategy.readyForLive ? (
                        <button 
                          className="bg-green-500 dark:bg-[var(--success-color)] text-white px-3 py-1 rounded text-xs hover:bg-green-600 flex items-center"
                          onClick={() => setActiveTab('live')}
                        >
                          Promote to Live <ArrowRight className="w-3 h-3 ml-1" />
                        </button>
                      ) : (
                        <button 
                          className="bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded text-xs cursor-not-allowed"
                          disabled
                        >
                          Not Ready
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {activeTab === 'live' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Live Trading Strategies</h2>
            <div className="bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-500 px-3 py-1 rounded text-sm font-medium">
              Trading with real money
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-[var(--card-bg)]">
              <thead className="bg-gray-50 dark:bg-[var(--sidebar-bg)]">
                <tr>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Return</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Max Drawdown</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sharpe</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Win Rate</th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-[var(--border-color)]">
                {liveStrategies.map((strategy, idx) => (
                  <tr key={idx}>
                    <td className="py-4 px-4 text-sm font-medium text-gray-900 dark:text-white">{strategy.name}</td>
                    <td className={`py-4 px-4 text-sm ${getStatusColor(strategy.status)}`}>{strategy.status}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.return > 0 ? `${strategy.metrics.return}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.maxDrawdown > 0 ? `${strategy.metrics.maxDrawdown}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.sharpe > 0 ? strategy.metrics.sharpe.toFixed(2) : '-'}</td>
                    <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{strategy.metrics.winRate > 0 ? `${strategy.metrics.winRate}%` : '-'}</td>
                    <td className="py-4 px-4 text-sm">
                      <div className="flex space-x-2">
                        <button 
                          className="bg-yellow-500 dark:bg-[var(--warning-color)] text-white px-3 py-1 rounded text-xs hover:bg-yellow-600"
                        >
                          Pause
                        </button>
                        <button 
                          className="bg-red-500 dark:bg-[var(--danger-color)] text-white px-3 py-1 rounded text-xs hover:bg-red-600"
                        >
                          Stop
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
