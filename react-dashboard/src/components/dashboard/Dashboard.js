import React from 'react';
import PortfolioSummary from './PortfolioSummary';
import PerformanceChart from './PerformanceChart';
import ActiveStrategies from './ActiveStrategies';
import AIAssistant from './AIAssistant';
import RecentActivity from './RecentActivity';
import MarketOverview from './MarketOverview';

const Dashboard = () => {
  return (
    <div>
      <h1>Trading Dashboard</h1>
      
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
