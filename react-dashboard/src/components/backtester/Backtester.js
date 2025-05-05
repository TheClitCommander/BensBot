import React from 'react';
import CurrentTest from './CurrentTest';
import StrategyQueue from './StrategyQueue';
import ProcessingStats from './ProcessingStats';
import PerformanceMetrics from './PerformanceMetrics';

const Backtester = () => {
  return (
    <div>
      <h1>Strategy Backtester</h1>
      
      <div className="dashboard-grid">
        <CurrentTest />
        <ProcessingStats />
      </div>
      
      <div className="dashboard-grid">
        <StrategyQueue />
        <PerformanceMetrics />
      </div>
    </div>
  );
};

export default Backtester;
