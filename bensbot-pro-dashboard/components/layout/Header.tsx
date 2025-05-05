import { useState } from 'react';
import { 
  Bell, RefreshCw, TrendingUp, TrendingDown, 
  Database, Activity, User, Settings, LogOut 
} from 'lucide-react';

export default function Header() {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  
  // Mock status data
  const mongoStatus = "Connected";
  const marketStatus = true; // true = open, false = closed
  const tradingStatus = true; // true = active, false = inactive
  
  return (
    <header className="bg-white dark:bg-[var(--card-bg)] border-b border-gray-200 dark:border-[var(--border-color)]">
      <div className="px-4 py-3 flex items-center justify-between">
        {/* Left side - Time & Status */}
        <div className="flex items-center">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <div className="font-medium text-gray-900 dark:text-white">
              {new Date().toLocaleString('en-US', { 
                weekday: 'short', 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
            <div className="flex mt-1 space-x-4">
              <div className="flex items-center">
                <div className={`h-2 w-2 rounded-full ${mongoStatus === "Connected" ? 'bg-green-500' : 'bg-red-500'} mr-1`}></div>
                <span>MongoDB: {mongoStatus}</span>
              </div>
              <div className="flex items-center">
                <div className={`h-2 w-2 rounded-full ${marketStatus ? 'bg-green-500' : 'bg-red-500'} mr-1`}></div>
                <span>Market: {marketStatus ? 'Open' : 'Closed'}</span>
              </div>
              <div className="flex items-center">
                <div className={`h-2 w-2 rounded-full ${tradingStatus ? 'bg-green-500' : 'bg-red-500'} mr-1`}></div>
                <span>Trading: {tradingStatus ? 'Active' : 'Inactive'}</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right side - Actions */}
        <div className="flex items-center space-x-4">
          {/* Refresh button */}
          <button className="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 
                             dark:text-gray-400 dark:hover:text-white dark:hover:bg-[var(--card-bg)]">
            <RefreshCw className="h-5 w-5" />
          </button>
          
          {/* Notifications */}
          <button className="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 
                             dark:text-gray-400 dark:hover:text-white dark:hover:bg-[var(--card-bg)] relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-0 right-0 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
              3
            </span>
          </button>
          
          {/* Market indicator */}
          <div className="px-3 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-500 
                          rounded-full flex items-center text-sm font-medium">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>Bullish</span>
          </div>
          
          {/* Profile menu */}
          <div className="relative">
            <button 
              className="flex items-center space-x-2 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[var(--card-bg)]"
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            >
              <div className="h-8 w-8 rounded-full bg-blue-500 dark:bg-[var(--accent-color)] text-white flex items-center justify-center">
                <User className="h-5 w-5" />
              </div>
            </button>
            
            {isProfileMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-[var(--card-bg)] rounded-md shadow-lg border border-gray-200 dark:border-[var(--border-color)]">
                <div className="py-1">
                  <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[var(--sidebar-bg)]">
                    <User className="inline-block h-4 w-4 mr-2" />
                    Profile
                  </a>
                  <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[var(--sidebar-bg)]">
                    <Settings className="inline-block h-4 w-4 mr-2" />
                    Settings
                  </a>
                  <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[var(--sidebar-bg)]">
                    <LogOut className="inline-block h-4 w-4 mr-2" />
                    Sign out
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
