import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, BarChart2, Zap, LineChart, Briefcase, 
  Bell, FileText, Settings, DollarSign, Activity
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  
  const navigation = [
    { name: 'Overview', href: '/dashboard', icon: Home },
    { name: 'Strategy Pipeline', href: '/dashboard/pipeline', icon: BarChart2 },
    { name: 'Signals & Approvals', href: '/dashboard/signals', icon: Zap },
    { name: 'Orders & Positions', href: '/dashboard/positions', icon: Briefcase },
    { name: 'Analytics', href: '/dashboard/analytics', icon: LineChart },
    { name: 'Logs', href: '/dashboard/logs', icon: FileText },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="flex flex-col w-64 bg-white dark:bg-[var(--sidebar-bg)] border-r border-gray-200 dark:border-[var(--border-color)]">
      {/* Logo */}
      <div className="px-6 pt-6 pb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <DollarSign className="h-8 w-8 text-blue-500 dark:text-[var(--accent-color)] mr-2" />
          BensBot Pro
        </h1>
      </div>
      
      {/* Account selection */}
      <div className="px-4 py-2 border-b border-gray-200 dark:border-[var(--border-color)]">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-1">
          Account
        </label>
        <select className="w-full bg-gray-100 dark:bg-[var(--card-bg)] border border-gray-200 dark:border-[var(--border-color)] rounded p-2 text-sm">
          <option value="all">All Accounts</option>
          <option value="live">Live Trading</option>
          <option value="paper">Paper Trading</option>
          <option value="backtest">Backtest</option>
        </select>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 pt-4 pb-4 overflow-y-auto">
        <div className="px-2 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`nav-button ${isActive ? 'active' : ''} flex items-center`}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </nav>
      
      {/* Key metrics */}
      <div className="p-4 border-t border-gray-200 dark:border-[var(--border-color)]">
        <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
          Account Status
        </h2>
        <div className="grid grid-cols-2 gap-2">
          <div className="metric-tile">
            <p className="metric-label">Balance</p>
            <p className="metric-value">$124,680</p>
          </div>
          <div className="metric-tile">
            <p className="metric-label">P&L</p>
            <p className="metric-value">+$1,245</p>
            <p className="metric-change positive">+1.2%</p>
          </div>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <div className="metric-tile">
            <p className="metric-label">Positions</p>
            <p className="metric-value">8</p>
          </div>
          <div className="metric-tile">
            <p className="metric-label">Win Rate</p>
            <p className="metric-value">68.5%</p>
          </div>
        </div>
        
        {/* Trading controls */}
        <div className="mt-4">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            Trading Controls
          </h2>
          <div className="grid grid-cols-2 gap-2">
            <button className="bg-green-500 dark:bg-[var(--success-color)] text-white px-3 py-2 rounded text-sm font-medium hover:bg-green-600 flex items-center justify-center">
              <Activity className="w-4 h-4 mr-1" />
              Start
            </button>
            <button className="bg-red-500 dark:bg-[var(--danger-color)] text-white px-3 py-2 rounded text-sm font-medium hover:bg-red-600 flex items-center justify-center">
              <Activity className="w-4 h-4 mr-1" />
              Stop
            </button>
          </div>
          <button className="mt-2 w-full bg-yellow-500 dark:bg-[var(--warning-color)] text-white px-3 py-2 rounded text-sm font-medium hover:bg-yellow-600 flex items-center justify-center">
            ⚠️ EMERGENCY STOP
          </button>
        </div>
        
        {/* Version */}
        <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
          <p>BensBot Pro v1.0</p>
          <p>{new Date().toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
}
