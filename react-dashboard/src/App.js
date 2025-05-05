import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './components/dashboard/Dashboard';
import Backtester from './components/backtester/Backtester';
import NewsAnalysis from './components/news/NewsAnalysis';
import Developer from './components/developer/Developer';

function App() {
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
}

export default App;
