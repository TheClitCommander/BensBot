import React, { useState } from 'react';
import './App.css';

// Import layout components
import Sidebar from './components/layout/Sidebar';

// Import dashboard components
import Dashboard from './components/dashboard/Dashboard';

// Import backtester components
import Backtester from './components/backtester/Backtester';

// Import news components
import NewsAnalysis from './components/news/NewsAnalysis';

// Import developer components
import Developer from './components/developer/Developer';

// Import settings page
import Settings from './pages/Settings';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  // Render the active component based on the selected tab
  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'Dashboard':
        return <Dashboard />;
      case 'Backtester':
        return <Backtester />;
      case 'News/Predictions':
        return <NewsAnalysis />;
      case 'Developer':
        return <Developer />;
      case 'Settings':
        return <Settings />;
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
