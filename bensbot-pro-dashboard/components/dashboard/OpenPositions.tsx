import { useState } from 'react';

// Sample data - this would be fetched from MongoDB in production
const initialPositions = [
  {
    id: 1,
    symbol: 'AAPL',
    strategy: 'Momentum',
    direction: 'LONG',
    entryPrice: 180.45,
    currentPrice: 182.45,
    quantity: 10,
    pnl: 200.00,
    pnlPercent: 1.1
  },
  {
    id: 2,
    symbol: 'MSFT',
    strategy: 'Momentum',
    direction: 'LONG',
    entryPrice: 410.30,
    currentPrice: 415.30,
    quantity: 5,
    pnl: 250.00,
    pnlPercent: 1.2
  },
  {
    id: 3,
    symbol: 'TSLA',
    strategy: 'Mean Reversion',
    direction: 'SHORT',
    entryPrice: 190.50,
    currentPrice: 188.20,
    quantity: 20,
    pnl: 46.00,
    pnlPercent: 1.2
  }
];

export default function OpenPositions() {
  const [positions, setPositions] = useState(initialPositions);
  
  const handleClosePosition = (id: number) => {
    // In a real app, this would call an API to close the position
    setPositions(positions.filter(position => position.id !== id));
    // Then possibly show a notification
  };
  
  return (
    <div className="dashboard-card">
      <h2 className="card-title">Open Positions</h2>
      
      {positions.length === 0 ? (
        <div className="text-center py-10 text-gray-500 dark:text-gray-400">
          No open positions
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white dark:bg-[var(--card-bg)]">
            <thead className="bg-gray-50 dark:bg-[var(--sidebar-bg)]">
              <tr>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Symbol</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Strategy</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Direction</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quantity</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Entry Price</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Current Price</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">P&L</th>
                <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-[var(--border-color)]">
              {positions.map((position) => (
                <tr key={position.id}>
                  <td className="py-4 px-4 text-sm font-medium text-gray-900 dark:text-white">{position.symbol}</td>
                  <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{position.strategy}</td>
                  <td className={`py-4 px-4 text-sm font-medium ${
                    position.direction === 'LONG' 
                      ? 'text-green-500 dark:text-green-400' 
                      : 'text-red-500 dark:text-red-400'
                  }`}>
                    {position.direction}
                  </td>
                  <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{position.quantity}</td>
                  <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">${position.entryPrice.toFixed(2)}</td>
                  <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">${position.currentPrice.toFixed(2)}</td>
                  <td className={`py-4 px-4 text-sm ${
                    position.pnl >= 0 
                      ? 'text-green-500 dark:text-green-400' 
                      : 'text-red-500 dark:text-red-400'
                  }`}>
                    {position.pnl >= 0 ? '+' : ''}${Math.abs(position.pnl).toFixed(2)} ({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(1)}%)
                  </td>
                  <td className="py-4 px-4 text-sm">
                    <button 
                      className="bg-red-500 dark:bg-[var(--danger-color)] text-white px-3 py-1 rounded text-xs hover:bg-red-600"
                      onClick={() => handleClosePosition(position.id)}
                    >
                      Close
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
