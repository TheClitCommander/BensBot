import PortfolioPerformance from '@/components/dashboard/PortfolioPerformance';
import StrategyAllocation from '@/components/dashboard/StrategyAllocation';
import StrategyPerformance from '@/components/dashboard/StrategyPerformance';
import MarketContext from '@/components/dashboard/MarketContext';
import RecentNotifications from '@/components/dashboard/RecentNotifications';

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard Overview</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Portfolio Performance Chart */}
        <PortfolioPerformance />
        
        {/* Strategy Allocation */}
        <StrategyAllocation />
        
        {/* Strategy Performance Comparison */}
        <div className="md:col-span-2">
          <StrategyPerformance />
        </div>
        
        {/* Market Context */}
        <MarketContext />
        
        {/* Recent Notifications */}
        <RecentNotifications />
      </div>
    </div>
  );
}
