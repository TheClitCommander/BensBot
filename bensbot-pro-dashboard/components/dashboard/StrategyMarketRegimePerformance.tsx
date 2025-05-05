import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Sample data - this would be fetched from MongoDB in production
const marketRegimeData = [
  { name: 'Bullish', Momentum: 80, MeanReversion: 60, TrendFollowing: 85, Volatility: 58 },
  { name: 'Bearish', Momentum: 45, MeanReversion: 75, TrendFollowing: 40, Volatility: 68 },
  { name: 'Sideways', Momentum: 58, MeanReversion: 82, TrendFollowing: 55, Volatility: 62 },
  { name: 'Volatile', Momentum: 48, MeanReversion: 55, TrendFollowing: 52, Volatility: 78 },
];

export default function StrategyMarketRegimePerformance() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Strategy Win Rate by Market Regime</h2>
      <p className="text-gray-500 dark:text-gray-400 mb-4">
        How different strategies perform in various market conditions.
      </p>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={marketRegimeData}
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
              formatter={(value) => [`${value}%`, 'Win Rate']}
              contentStyle={{ 
                backgroundColor: 'var(--card-bg)', 
                borderColor: 'var(--border-color)',
                color: 'var(--text-color)'
              }}
            />
            <Legend wrapperStyle={{ color: 'var(--text-color)' }} />
            <Bar dataKey="Momentum" fill="#0088FE" radius={[4, 4, 0, 0]} />
            <Bar dataKey="MeanReversion" fill="#00C49F" radius={[4, 4, 0, 0]} />
            <Bar dataKey="TrendFollowing" fill="#FFBB28" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Volatility" fill="#FF8042" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
