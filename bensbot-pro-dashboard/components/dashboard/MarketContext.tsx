import { TrendingUp } from 'lucide-react';

export default function MarketContext() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Market Context</h2>
      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg mb-4">
        <div className="flex items-center mb-2">
          <TrendingUp className="text-green-500 mr-2" />
          <h3 className="text-lg font-medium text-green-700 dark:text-green-400">Current Market Regime: Bullish</h3>
        </div>
        <p className="text-gray-600 dark:text-gray-300">
          Markets showing positive momentum with technology stocks leading. Potential volatility around upcoming Fed meeting.
        </p>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">VIX (Volatility):</span>
          <span className="text-gray-800 dark:text-gray-200">15.7 <span className="text-green-500">(-1.2)</span></span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">Top Performing Sector:</span>
          <span className="text-gray-800 dark:text-gray-200">Technology <span className="text-green-500">+2.3%</span></span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">Trend Strength:</span>
          <span className="text-gray-800 dark:text-gray-200">0.82 (Strong)</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">SPY:</span>
          <span className="text-green-500">+0.8%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">QQQ:</span>
          <span className="text-green-500">+1.2%</span>
        </div>
      </div>
    </div>
  );
}
