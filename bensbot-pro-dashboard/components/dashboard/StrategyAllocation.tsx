import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

// Sample data - this would be fetched from MongoDB in production
const strategyAllocationData = [
  { name: 'Momentum', value: 20 },
  { name: 'Mean Reversion', value: 15 },
  { name: 'Trend Following', value: 25 },
  { name: 'Breakout Swing', value: 20 },
  { name: 'Volatility Breakout', value: 10 },
  { name: 'Option Spreads', value: 10 },
];

// Chart colors
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export default function StrategyAllocation() {
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Current Strategy Allocation</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={strategyAllocationData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              label={({name, value}) => `${name}: ${value}%`}
            >
              {strategyAllocationData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value) => `${value}%`}
              contentStyle={{ 
                backgroundColor: 'var(--card-bg)', 
                borderColor: 'var(--border-color)',
                color: 'var(--text-color)'
              }}
            />
            <Legend 
              layout="vertical" 
              verticalAlign="middle" 
              align="right"
              wrapperStyle={{ color: 'var(--text-color)' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
