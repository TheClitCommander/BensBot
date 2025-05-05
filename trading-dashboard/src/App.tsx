import React, { useState } from 'react';
import './App.css';

const Sidebar: React.FC<{
  activeTab: string;
  setActiveTab: (tab: string) => void;
}> = ({ activeTab, setActiveTab }) => {
  // Navigation items
  const navItems = [
    { name: 'Dashboard', icon: 'dashboard' },
    { name: 'Backtester', icon: 'assessment' },
    { name: 'News/Analysis', icon: 'trending_up' },
    { name: 'Developer', icon: 'code' },
  ];

  return (
    <div className="sidebar">
      <div className="logo-container">
        <div className="logo">
          <img 
            src="https://via.placeholder.com/150x80?text=BensBot" 
            alt="BensBot Logo" 
            style={{ width: '100%' }}
          />
        </div>
        <div className="logo-text">BensBot Trading</div>
      </div>
      
      <nav>
        {navItems.map((item) => (
          <div
            key={item.name}
            className={`nav-link ${activeTab === item.name ? 'active' : ''}`}
            onClick={() => setActiveTab(item.name)}
          >
            <span className="material-icons" style={{ marginRight: '8px', verticalAlign: 'middle' }}>
              {item.icon}
            </span>
            {item.name}
          </div>
        ))}
      </nav>
      
      <div style={{ marginTop: 'auto', padding: '1rem 0' }}>
        <div style={{ fontSize: '0.8rem', color: '#9e9e9e', marginBottom: '1rem' }}>
          © 2025 BensBot Trading Platform
        </div>
        <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>
          Version 2.3.4
        </div>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1>Trading Dashboard</h1>
      
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">Portfolio Summary</h2>
          <div className="card-content">
            <div className="stats-container">
              <div className="stat-item">
                <div className="stat-value">$852,437.29</div>
                <div className="stat-label">Total Value</div>
              </div>
              <div className="stat-item">
                <div className="stat-value positive-value">+$12,483.57 (+1.49%)</div>
                <div className="stat-label">Daily Change</div>
              </div>
              <div className="stat-item">
                <div className="stat-value positive-value">+7.2%</div>
                <div className="stat-label">Monthly Return</div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="card-header">Market Overview</h2>
          <div className="card-content">
            <div className="stats-container">
              <div className="stat-item">
                <div className="stat-value">S&P 500: <span className="positive-value">+0.8%</span></div>
              </div>
              <div className="stat-item">
                <div className="stat-value">Nasdaq: <span className="positive-value">+1.2%</span></div>
              </div>
              <div className="stat-item">
                <div className="stat-value">BTC: <span className="positive-value">+1.6%</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">Active Strategies</h2>
          <div className="card-content">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Performance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Tech Momentum</td>
                  <td className="positive-value">+21.3%</td>
                  <td><span className="badge success">Active</span></td>
                </tr>
                <tr>
                  <td>BTC Volatility Edge</td>
                  <td className="positive-value">+32.1%</td>
                  <td><span className="badge success">Active</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="card-header">Current Backtest</h2>
          <div className="card-content">
            <div style={{ marginBottom: '12px' }}>
              <div className="progress-bar" style={{ height: '10px', margin: '8px 0' }}>
                <div className="progress-bar-fill info" style={{ width: '68%' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <small>68% Complete</small>
                <small>ETA: 14:30:00</small>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>56.4%</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Win Rate</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>1.82</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Profit Factor</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Backtester: React.FC = () => {
  return (
    <div>
      <h1>Strategy Backtester</h1>
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">Current Backtest</h2>
          <div className="card-content">
            <div style={{ marginBottom: '12px' }}>
              <div className="progress-bar" style={{ height: '10px', margin: '8px 0' }}>
                <div className="progress-bar-fill info" style={{ width: '68%' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <small>68% Complete</small>
                <small>ETA: 2025-05-04 14:30:00</small>
              </div>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
              <div>
                <strong>Started:</strong> 2025-05-04 12:15:32
              </div>
              <div>
                <strong>Elapsed:</strong> 01:30:15
              </div>
              <div>
                <strong>Test Period:</strong> 2020-01-01 to 2025-05-01
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <strong>Symbols:</strong> AAPL, MSFT, AMZN, GOOGL, META
            </div>

            <h4>Initial Results</h4>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>56.4%</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Win Rate</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>1.82</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Profit Factor</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00C853' }}>1.45</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Sharpe Ratio</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF5252' }}>12.3%</div>
                <div style={{ fontSize: '12px', color: '#787878' }}>Max Drawdown</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const NewsAnalysis: React.FC = () => {
  return (
    <div>
      <h1>News & Market Analysis</h1>
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">Market Sentiment</h2>
          <div className="card-content">
            <p>Markets are showing <strong style={{ color: '#4CAF50' }}>bullish</strong> momentum today, with technology and financial sectors leading gains.</p>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span>Overall Market Sentiment</span>
                <span>Bullish</span>
              </div>
              <div className="progress-bar">
                <div className="progress-bar-fill success" style={{ width: '72%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Developer: React.FC = () => {
  return (
    <div>
      <h1>Developer Tools</h1>
      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-header">System Logs</h2>
          <div className="card-content">
            <div style={{ 
              backgroundColor: '#1e1e1e', 
              borderRadius: '4px', 
              height: '300px',
              overflow: 'auto',
              padding: '12px',
              fontFamily: 'monospace',
              fontSize: '0.9rem'
            }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #333' }}>
                <span style={{ color: '#9e9e9e' }}>14:55:21.342</span>
                <span className="badge info" style={{ margin: '0 8px' }}>INFO</span>
                <span style={{ color: '#e0e0e0' }}>Strategy "Tech Momentum" successfully updated parameters</span>
              </div>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #333' }}>
                <span style={{ color: '#9e9e9e' }}>14:54:45.123</span>
                <span className="badge warning" style={{ margin: '0 8px' }}>WARN</span>
                <span style={{ color: '#e0e0e0' }}>Rate limit approaching for Alpha Vantage API</span>
              </div>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #333' }}>
                <span style={{ color: '#9e9e9e' }}>14:53:12.856</span>
                <span className="badge danger" style={{ margin: '0 8px' }}>ERROR</span>
                <span style={{ color: '#e0e0e0' }}>Failed to execute order for AMZN</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  // Render the active component based on the selected tab
  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'Dashboard':
        return <Dashboard />;
      case 'Backtester':
        return <Backtester />;
      case 'News/Analysis':
        return <NewsAnalysis />;
      case 'Developer':
        return <Developer />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {renderActiveComponent()}
      </main>
    </div>
  );
};

export default App;
