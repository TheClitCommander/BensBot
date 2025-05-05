import StrategyFeatureImportance from '@/components/dashboard/StrategyFeatureImportance';
import BacktestVsLivePerformance from '@/components/dashboard/BacktestVsLivePerformance';
import StrategyMarketRegimePerformance from '@/components/dashboard/StrategyMarketRegimePerformance';

export default function AnalyticsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trading Analytics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strategy Feature Importance */}
        <div className="md:col-span-2">
          <StrategyFeatureImportance />
        </div>
        
        {/* Backtest vs. Live Performance */}
        <BacktestVsLivePerformance />
        
        {/* Strategy Win Rate by Market Regime */}
        <StrategyMarketRegimePerformance />
      </div>
    </div>
  );
}
