import axios from 'axios';

// Backtester interfaces
export interface BacktestStrategy {
  id: string;
  name: string;
  description: string;
  status: 'In Queue' | 'In Progress' | 'Completed' | 'Failed';
  priority: 'High' | 'Medium' | 'Low';
  estimatedStart: string;
  assets: string[];
  parameters: Record<string, any>;
  complexity: 'High' | 'Medium' | 'Low';
  createdAt: string;
  updatedAt: string;
}

export interface TestResults {
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  sortino?: number;
  maxDrawdown: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  averageWin: number;
  averageLoss: number;
  expectancy: number;
  annualizedReturn: number;
}

export interface BacktestData {
  id: string;
  progress: number;
  eta: string;
  startedAt: string;
  elapsed: string;
  testPeriod: string;
  symbols: string[];
  parameters: Record<string, any>;
  results?: TestResults;
  executionStage: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  errorMessage?: string;
}

export interface ProcessingStats {
  cpu: number;
  memory: number;
  disk: number;
  concurrentTests: number;
  completedToday: number;
  averageDuration: string;
  queueLength: number;
}

export interface PerformanceAnalysis {
  returns: {
    period: string;
    value: number;
  }[];
  drawdowns: {
    start: string;
    end: string;
    depth: number;
    duration: string;
  }[];
  monthlySharpe: number;
  bestDay: {
    date: string;
    return: number;
  };
  worstDay: {
    date: string;
    return: number;
  };
}

// Get API URL from environment if available
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5003';

// Initialize API client
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add request interceptor
apiClient.interceptors.request.use(
  config => {
    // If we have a token in local storage, attach it to the request
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Backtester API methods
export const backtesterApi = {
  // Get current test in progress
  getCurrentTest: async (): Promise<BacktestData | null> => {
    try {
      const response = await apiClient.get('/api/ml-backtesting/current');
      if (response.data && response.data.success) {
        return response.data.backtest;
      }
      throw new Error(response.data?.error || 'Failed to fetch current backtest');
    } catch (error) {
      console.error('Error fetching current backtest:', error);
      
      // Return mock data for development
      return {
        id: 'BT-2025050501',
        progress: 68,
        eta: '2025-05-05 14:30:00',
        startedAt: '2025-05-05 12:15:32',
        elapsed: '01:30:15',
        testPeriod: '2020-01-01 to 2025-05-01',
        symbols: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'],
        parameters: {
          lookbackPeriod: 20,
          takeProfit: 2.5,
          stopLoss: 1.2,
          timeframeMinutes: 60
        },
        executionStage: 'Analyzing pattern performance',
        status: 'running',
        results: {
          winRate: 56.4,
          profitFactor: 1.82,
          sharpeRatio: 1.45,
          sortino: 1.35,
          maxDrawdown: 12.3,
          totalTrades: 145,
          winningTrades: 82,
          losingTrades: 63,
          averageWin: 1.92,
          averageLoss: 0.85,
          expectancy: 0.67,
          annualizedReturn: 18.2
        }
      };
    }
  },
  
  // Get strategies in queue
  getStrategyQueue: async (): Promise<BacktestStrategy[]> => {
    try {
      const response = await apiClient.get('/api/ml-strategy-suggestions');
      if (response.data && response.data.success) {
        return response.data.suggestions.map((suggestion: any) => ({
          id: suggestion.id || `ST-${Math.floor(Math.random() * 10000)}`,
          name: suggestion.name,
          description: suggestion.description || 'ML-generated strategy based on current market conditions',
          status: 'In Queue',
          priority: suggestion.priority || 'Medium',
          estimatedStart: new Date(Date.now() + 3600000).toISOString(),
          assets: suggestion.assets || ['SPY', 'QQQ', 'AAPL'],
          parameters: suggestion.parameters || {},
          complexity: suggestion.complexity || 'Medium',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }));
      }
      throw new Error(response.data?.error || 'Failed to fetch strategy queue');
    } catch (error) {
      console.error('Error fetching backtest queue:', error);
      
      // Return mock data for development
      return [
        {
          id: 'ST-427',
          name: 'ML-Enhanced Mean Reversion',
          description: 'Uses machine learning to identify optimal entry and exit points for mean reversion trades',
          status: 'In Queue',
          priority: 'High',
          estimatedStart: '2025-05-05 15:30:00',
          assets: ['SPY', 'QQQ', 'IWM'],
          parameters: {
            lookbackPeriod: 20,
            stdDevThreshold: 2.0,
            minRSI: 30,
            maxRSI: 70
          },
          complexity: 'High',
          createdAt: '2025-05-04 18:20:10',
          updatedAt: '2025-05-04 18:20:10'
        },
        {
          id: 'ST-428',
          name: 'Adaptive Momentum with Volatility Control',
          description: 'Dynamic momentum strategy that adjusts position sizing based on market volatility',
          status: 'In Queue',
          priority: 'Medium',
          estimatedStart: '2025-05-05 16:15:00',
          assets: ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META'],
          parameters: {
            momentumPeriod: 50,
            volatilityWindow: 20,
            riskAdjustment: 0.5
          },
          complexity: 'Medium',
          createdAt: '2025-05-04 19:05:22',
          updatedAt: '2025-05-04 19:05:22'
        },
        {
          id: 'ST-429',
          name: 'Multi-timeframe Breakout Detection',
          description: 'Identifies and trades breakouts confirmed across multiple timeframes',
          status: 'In Queue',
          priority: 'Medium',
          estimatedStart: '2025-05-05 17:00:00',
          assets: ['BTC-USD', 'ETH-USD', 'SOL-USD'],
          parameters: {
            primaryTimeframe: 60,
            confirmationTimeframe: 240,
            volumeThreshold: 1.5
          },
          complexity: 'High',
          createdAt: '2025-05-04 20:10:45',
          updatedAt: '2025-05-04 20:10:45'
        },
        {
          id: 'ST-430',
          name: 'Sector Rotation Algorithm',
          description: 'Rotates capital between sectors based on relative strength and economic indicators',
          status: 'In Queue',
          priority: 'Low',
          estimatedStart: '2025-05-05 18:30:00',
          assets: ['XLF', 'XLK', 'XLE', 'XLV', 'XLP', 'XLI', 'XLY', 'XLB', 'XLU', 'XLRE', 'XLC'],
          parameters: {
            rotationPeriod: 30,
            minStrength: 0.75,
            maxSectors: 3
          },
          complexity: 'High',
          createdAt: '2025-05-04 22:30:15',
          updatedAt: '2025-05-04 22:30:15'
        }
      ];
    }
  },
  
  // Get server processing stats
  getProcessingStats: async (): Promise<ProcessingStats> => {
    try {
      const response = await apiClient.get('/api/ml-model-insights');
      if (response.data && response.data.success) {
        // Convert API response to our stats format
        const systemInfo = response.data.system_info || {};
        return {
          cpu: systemInfo.cpu_utilization || 78,
          memory: systemInfo.memory_utilization || 65,
          disk: systemInfo.disk_utilization || 42,
          concurrentTests: systemInfo.concurrent_tests || 1,
          completedToday: systemInfo.completed_today || 7,
          averageDuration: systemInfo.average_duration || '01:42:35',
          queueLength: systemInfo.queue_length || 4
        };
      }
      throw new Error(response.data?.error || 'Failed to fetch processing stats');
    } catch (error) {
      console.error('Error fetching processing stats:', error);
      
      // Return mock data for development
      return {
        cpu: 78,
        memory: 65,
        disk: 42,
        concurrentTests: 1,
        completedToday: 7,
        averageDuration: '01:42:35',
        queueLength: 4
      };
    }
  },
  
  // Get performance metrics for a completed test
  getPerformanceMetrics: async (testId: string): Promise<PerformanceAnalysis> => {
    try {
      const response = await apiClient.get(`/api/ml-backtest-result/${testId}`);
      if (response.data && response.data.success) {
        const result = response.data.result;
        
        // Map API response to our performance analysis format
        return {
          returns: Object.entries(result.returns || {}).map(([period, value]: [string, any]) => ({
            period,
            value: parseFloat(value)
          })),
          drawdowns: (result.drawdowns || []).map((dd: any) => ({
            start: dd.start_date,
            end: dd.end_date,
            depth: dd.depth,
            duration: dd.duration
          })),
          monthlySharpe: result.monthly_sharpe || 1.22,
          bestDay: {
            date: result.best_day?.date || '2024-08-04',
            return: result.best_day?.return || 3.8
          },
          worstDay: {
            date: result.worst_day?.date || '2024-02-28',
            return: result.worst_day?.return || -4.2
          }
        };
      }
      throw new Error(response.data?.error || 'Failed to fetch performance metrics');
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      
      // Return mock data for development
      return {
        returns: [
          { period: '1D', value: 0.8 },
          { period: '1W', value: 2.4 },
          { period: '1M', value: 7.5 },
          { period: '3M', value: 12.2 },
          { period: '6M', value: 18.6 },
          { period: '1Y', value: 24.5 },
          { period: 'YTD', value: 14.2 }
        ],
        drawdowns: [
          { start: '2024-02-15', end: '2024-03-10', depth: 12.3, duration: '24d' },
          { start: '2024-06-22', end: '2024-07-15', depth: 8.7, duration: '23d' },
          { start: '2025-01-05', end: '2025-01-18', depth: 5.2, duration: '13d' }
        ],
        monthlySharpe: 1.22,
        bestDay: {
          date: '2024-08-04',
          return: 3.8
        },
        worstDay: {
          date: '2024-02-28',
          return: -4.2
        }
      };
    }
  },
  
  // Submit a new strategy for backtesting
  submitStrategy: async (strategy: Partial<BacktestStrategy>): Promise<BacktestStrategy> => {
    try {
      const response = await apiClient.post('/api/ml-backtesting/run', {
        strategy_name: strategy.name,
        description: strategy.description,
        assets: strategy.assets,
        parameters: strategy.parameters,
        priority: strategy.priority || 'Medium',
        complexity: strategy.complexity || 'Medium'
      });
      
      if (response.data && response.data.success) {
        return {
          id: response.data.strategy_id,
          name: strategy.name || '',
          description: strategy.description || '',
          status: 'In Queue',
          priority: strategy.priority || 'Medium',
          estimatedStart: new Date(Date.now() + 1800000).toISOString(),
          assets: strategy.assets || [],
          parameters: strategy.parameters || {},
          complexity: strategy.complexity || 'Medium',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
      }
      
      throw new Error(response.data?.error || 'Failed to submit strategy for backtesting');
    } catch (error) {
      console.error('Error submitting strategy:', error);
      throw new Error('Failed to submit strategy for backtesting');
    }
  },
  
  // Control actions for backtest
  controlBacktest: async (action: 'pause' | 'resume' | 'cancel', testId: string): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await apiClient.post('/api/ml-backtesting/control', { 
        action,
        backtest_id: testId
      });
      
      if (response.data) {
        return {
          success: response.data.success || false,
          message: response.data.message || `Backtest ${action} action completed`
        };
      }
      
      return { success: false, message: `Failed to ${action} backtest` };
    } catch (error) {
      console.error(`Error executing ${action} action on backtest:`, error);
      return { success: false, message: `Failed to ${action} backtest` };
    }
  },
  
  // Request live deployment of a successful strategy (requires approval)
  requestLiveDeployment: async (strategyId: string, params: { accountId: string, allocation: number, risk: number }): Promise<{ success: boolean; deploymentId?: string; message: string; requiresApproval: boolean }> => {
    try {
      const response = await apiClient.post('/api/ml-strategy-deploy', { 
        strategy_id: strategyId,
        account_id: params.accountId,
        allocation_percentage: params.allocation,
        risk_level: params.risk
      });
      
      if (response.data) {
        return {
          success: response.data.success || false,
          deploymentId: response.data.deployment_id,
          message: response.data.message || 'Deployment request submitted',
          requiresApproval: response.data.requires_approval !== false // Default to true for safety
        };
      }
      
      return { 
        success: false, 
        message: 'Failed to request live deployment', 
        requiresApproval: true 
      };
    } catch (error) {
      console.error('Error requesting live deployment:', error);
      return { 
        success: false, 
        message: 'Failed to request live deployment', 
        requiresApproval: true 
      };
    }
  },
  
  // Check deployment approval status
  checkDeploymentStatus: async (deploymentId: string): Promise<{ status: 'pending' | 'approved' | 'rejected' | 'deployed'; message: string }> => {
    try {
      const response = await apiClient.get(`/api/ml-strategy-deploy/status/${deploymentId}`);
      
      if (response.data && response.data.success) {
        return {
          status: response.data.deployment_status || 'pending',
          message: response.data.message || 'Deployment status retrieved'
        };
      }
      
      throw new Error(response.data?.error || 'Failed to check deployment status');
    } catch (error) {
      console.error('Error checking deployment status:', error);
      return { 
        status: 'pending', 
        message: 'Deployment approval status unavailable' 
      };
    }
  },
  
  // Get available trading accounts
  getAccounts: async (): Promise<{ id: string; name: string; type: string; balance: number }[]> => {
    try {
      const response = await apiClient.get('/api/trading_accounts');
      
      if (response.data && Array.isArray(response.data)) {
        return response.data.map((account: any) => ({
          id: account.id || account.account_id,
          name: account.name || `${account.broker} ${account.account_type}`,
          type: account.account_type || 'unknown',
          balance: account.balance || 0
        }));
      }
      
      throw new Error('Failed to fetch trading accounts');
    } catch (error) {
      console.error('Error fetching trading accounts:', error);
      
      // Return mock data
      return [
        { id: 'paper-account-1', name: 'Paper Trading - Default', type: 'paper', balance: 100000 },
        { id: 'paper-account-2', name: 'Paper Trading - Aggressive', type: 'paper', balance: 50000 },
        { id: 'live-account-1', name: 'Tradier - Live', type: 'live', balance: 25000 }
      ];
    }
  }
};

export default backtesterApi;
