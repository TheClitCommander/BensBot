import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Sample data - this would be fetched from MongoDB in production
const featureImportanceData = [
  { name: 'RSI (14)', Momentum: 18, MeanReversion: 25, TrendFollowing: 10, Volatility: 15 },
  { name: 'MACD', Momentum: 25, MeanReversion: 10, TrendFollowing: 30, Volatility: 12 },
  { name: 'Bollinger Bands', Momentum: 15, MeanReversion: 30, TrendFollowing: 8, Volatility: 18 },
  { name: 'Volume', Momentum: 20, MeanReversion: 15, TrendFollowing: 18, Volatility: 25 },
  { name: 'ATR', Momentum: 12, MeanReversion: 12, TrendFollowing: 15, Volatility: 30 },
  { name: 'Moving Averages', Momentum: 10, MeanReversion: 8, TrendFollowing: 25, Volatility: 10 },
];

export default function StrategyFeatureImportance() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Strategy Feature Importance</h2>
      <p className="text-gray-500 dark:text-gray-400 mb-4">
        This chart shows the relative importance of different technical indicators for each strategy's decision making.
      </p>
      
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={featureImportanceData}
            margin={{ top: 20, right: 30, left: 40, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis 
              type="number" 
              stroke="var(--text-color)" 
              tick={{ fill: 'var(--text-color)' }}
            />
            <YAxis 
              dataKey="name" 
              type="category" 
              scale="band" 
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
            <Bar dataKey="Momentum" fill="#0088FE" />
            <Bar dataKey="MeanReversion" fill="#00C49F" />
            <Bar dataKey="TrendFollowing" fill="#FFBB28" />
            <Bar dataKey="Volatility" fill="#FF8042" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
