import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Sample data - this would be fetched from MongoDB in production
const strategyPerformanceData = [
  { name: 'Momentum', winRate: 72, profitFactor: 2.1 },
  { name: 'Mean Reversion', winRate: 68, profitFactor: 1.8 },
  { name: 'Trend Following', winRate: 74, profitFactor: 2.2 },
  { name: 'Breakout Swing', winRate: 59, profitFactor: 1.5 },
  { name: 'Volatility Breakout', winRate: 62, profitFactor: 1.6 },
  { name: 'Option Spreads', winRate: 65, profitFactor: 1.7 },
];

export default function StrategyPerformance() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Strategy Performance</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart 
            data={strategyPerformanceData} 
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
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'var(--card-bg)', 
                borderColor: 'var(--border-color)',
                color: 'var(--text-color)'
              }}
            />
            <Legend wrapperStyle={{ color: 'var(--text-color)' }} />
            <Bar 
              dataKey="winRate" 
              fill="#0088FE" 
              name="Win Rate (%)" 
              radius={[4, 4, 0, 0]}
            />
            <Bar 
              dataKey="profitFactor" 
              fill="#00C49F" 
              name="Profit Factor" 
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
