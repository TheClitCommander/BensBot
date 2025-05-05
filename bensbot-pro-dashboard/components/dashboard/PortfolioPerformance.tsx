import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// Sample data - this would be fetched from your MongoDB in production
const performanceData = [
  { date: '2024-04-15', value: 100000 },
  { date: '2024-05-01', value: 102500 },
  { date: '2024-06-01', value: 101800 },
  { date: '2024-07-01', value: 105300 },
  { date: '2024-08-01', value: 107800 },
  { date: '2024-09-01', value: 106200 },
  { date: '2024-10-01', value: 110500 },
  { date: '2024-11-01', value: 114200 },
  { date: '2024-12-01', value: 118600 },
  { date: '2025-01-01', value: 120100 },
  { date: '2025-02-01', value: 122800 },
  { date: '2025-03-01', value: 123500 },
  { date: '2025-04-01', value: 124680 },
];

export default function PortfolioPerformance() {
  return (
    <div className="dashboard-card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="card-title">Portfolio Performance</h2>
        <div className="flex space-x-2">
          <select className="text-xs border border-gray-200 dark:border-[var(--border-color)] rounded p-1 bg-white dark:bg-[var(--card-bg)]">
            <option>1M</option>
            <option>3M</option>
            <option>6M</option>
            <option selected>1Y</option>
            <option>All</option>
          </select>
          <select className="text-xs border border-gray-200 dark:border-[var(--border-color)] rounded p-1 bg-white dark:bg-[var(--card-bg)]">
            <option>All Accounts</option>
            <option>Live</option>
            <option>Paper</option>
            <option>Backtest</option>
          </select>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={performanceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis 
              dataKey="date" 
              stroke="var(--text-color)" 
              tick={{ fill: 'var(--text-color)' }}
            />
            <YAxis 
              domain={['dataMin - 5000', 'dataMax + 5000']} 
              stroke="var(--text-color)" 
              tick={{ fill: 'var(--text-color)' }}
              tickFormatter={(value) => `$${value.toLocaleString()}`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'var(--card-bg)', 
                borderColor: 'var(--border-color)',
                color: 'var(--text-color)'
              }} 
              formatter={(value) => [`$${(value as number).toLocaleString()}`, 'Portfolio Value']}
            />
            <Legend wrapperStyle={{ color: 'var(--text-color)' }} />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="var(--accent-color)" 
              strokeWidth={2} 
              dot={false}
              activeDot={{ r: 6 }}
              name="Portfolio Value ($)" 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
