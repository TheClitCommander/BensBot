import React, { useState, useEffect } from 'react';
import PortfolioSummary from './PortfolioSummary';
import PerformanceChart from './PerformanceChart';
import ActiveStrategies from './ActiveStrategies';
import AIAssistant from './AIAssistant';
import RecentActivity from './RecentActivity';
import MarketOverview from './MarketOverview';
import BrokerStatus from './BrokerStatus';
import PortfolioSelector from './PortfolioSelector';
import '../settings/settings.css';

const Dashboard: React.FC = () => {
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
  
  // Load the previously selected portfolio from localStorage
  useEffect(() => {
    const savedPortfolio = localStorage.getItem('selected_portfolio_id');
    if (savedPortfolio) {
      setSelectedPortfolio(savedPortfolio);
    }
  }, []);
  
  const handlePortfolioChange = (portfolioId: string) => {
    console.log('Selected portfolio changed to:', portfolioId);
    setSelectedPortfolio(portfolioId);
    // Additional logic for portfolio change can be added here
  };

  return (
    <div>
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h1>Trading Dashboard</h1>
        </div>
        <div className="dashboard-controls">
          <PortfolioSelector onChange={handlePortfolioChange} />
          <BrokerStatus />
        </div>
      </div>
      
      <div className="dashboard-grid">
        <PortfolioSummary />
        <MarketOverview />
      </div>
      
      <div className="dashboard-grid">
        <PerformanceChart />
      </div>
      
      <div className="dashboard-grid">
        <ActiveStrategies />
        <RecentActivity />
      </div>
      
      <div className="dashboard-grid">
        <AIAssistant />
      </div>
    </div>
  );
};

export default Dashboard;
