import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Sample data - this would be fetched from MongoDB in production
const performanceComparisonData = [
  { name: 'Momentum', Backtest: 12.5, Paper: 8.5, Live: 3.2 },
  { name: 'Mean Reversion', Backtest: 9.8, Paper: 6.2, Live: 0 },
  { name: 'Volatility Breakout', Backtest: 14.2, Paper: 0, Live: 0 },
];

export default function BacktestVsLivePerformance() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Backtest vs. Live Performance</h2>
      <p className="text-gray-500 dark:text-gray-400 mb-4">
        Comparing strategy performance in backtesting vs. paper trading vs. live trading.
      </p>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={performanceComparisonData}
            margin={{ top: 5, right: 30, bottom: 5, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis 
              dataKey="name" 
              stroke="var(--text-color)" 
              tick={{ fill: 'var(--text-color)' }}
            />
            <YAxis 
              stroke="var(--text-color)" 
              tick={{ fill: 'var(--text-color)' }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              formatter={(value) => [`${value}%`, 'Return']}
              contentStyle={{ 
                backgroundColor: 'var(--card-bg)', 
                borderColor: 'var(--border-color)',
                color: 'var(--text-color)'
              }}
            />
            <Legend wrapperStyle={{ color: 'var(--text-color)' }} />
            <Bar dataKey="Backtest" fill="#0088FE" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Paper" fill="#00C49F" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Live" fill="#FFBB28" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
