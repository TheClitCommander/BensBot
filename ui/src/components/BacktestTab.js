import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, BrainCircuit, ArrowUpRight, ArrowDownRight, Zap, Activity,
  PlusCircle, Award, BarChart2, ChevronDown, Save, Users, Lightbulb, 
  Database, Newspaper
} from 'lucide-react';

/**
 * Autonomous ML Backtesting Interface Component
 */
const BacktestTab = () => {
  // State variables for backtesting results and UI
  const [topWinningStrategies, setTopWinningStrategies] = useState([]);
  const [topLosingStrategies, setTopLosingStrategies] = useState([]);
  const [collaborativeWinningStrategies, setCollaborativeWinningStrategies] = useState([]);
  const [collaborativeLosingStrategies, setCollaborativeLosingStrategies] = useState([]);
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [mlStatus, setMlStatus] = useState({
    isActive: false,
    dataSourcesActive: [],
    insights: []
  });
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [filterParams, setFilterParams] = useState({
    sector: 'all',
    marketCondition: 'all',
    timeRange: '1y'
  });

  // Fetch initial ML status on load
  useEffect(() => {
    fetchMlStatus();
    generateMockData(); // Initialize with some data
  }, []);

  // Fetch ML status from the backend
  const fetchMlStatus = async () => {
    try {
      const response = await fetch('/api/autonomous-ml-backtesting/status');
      const data = await response.json();
      
      setMlStatus({
        isActive: data.available,
        lastTrained: data.last_trained,
        modelVersion: data.model_version,
        strategyCount: data.strategy_count,
        dataSourcesActive: [
          { name: 'Historical Data', type: 'historical', active: true, status: 'Active' },
          { name: 'News API', type: 'news', active: true, status: 'Active' },
          { name: 'Technical Indicators', type: 'indicators', active: true, status: 'Active' }
        ],
        insights: [
          { title: 'Pattern Detected', description: 'Correlation between news sentiment and price action' },
          { title: 'Strategy Effectiveness', description: 'Moving average strategies performing well in current market' }
        ]
      });
    } catch (error) {
      console.error('Error fetching ML status:', error);
    }
  };

  // Run ML backtests
  const runAutonomousBacktests = async () => {
    setIsRunningTests(true);
    
    try {
      const response = await fetch('/api/autonomous-backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filterParams)
      });
      
      const data = await response.json();
      
      if (data.success && data.results) {
        // Update strategies
        setTopWinningStrategies(data.results.winning_strategies.slice(0, 3));
        setTopLosingStrategies(data.results.losing_strategies.slice(0, 3));
        
        // Update ML status with insights
        setMlStatus(prev => ({
          ...prev,
          lastRun: new Date().toISOString(),
          insights: data.results.ml_insights?.winning_patterns?.slice(0, 3).map(insight => ({
            title: 'Strategy Insight',
            description: insight
          })) || prev.insights
        }));
      }
    } catch (error) {
      console.error('Error running ML backtests:', error);
    } finally {
      setIsRunningTests(false);
    }
  };

  // Generate mock data for initial UI display
  const generateMockData = () => {
    // Mock winning strategies
    const winning = [
      {
        id: 1,
        strategy: {
          id: 'ml_strategy_1',
          name: 'News Sentiment Momentum v20250417',
          template: 'news_sentiment_momentum',
          params: {
            sentiment_threshold: 0.25,
            momentum_period: 5,
            holding_period: 4
          },
          risk_params: {
            risk_level: 'moderate',
            position_size: 0.1,
            stop_loss_percentage: 2.5,
            take_profit_percentage: 5.0
          },
          confidence_score: 0.85,
          reasoning: {
            summary: 'Selected based on positive news sentiment correlation',
            political_factors: ['Supportive policy outlook with potential positive impacts'],
            social_factors: ['Positive social responsibility factors detected'],
            economic_factors: ['Strong earnings expectations', 'Positive trend indicated by moving averages'],
            technical_indicators: [
              { name: 'RSI', signal: 'bullish', description: 'RSI showing upward momentum' },
              { name: 'Moving Averages', signal: 'bullish', description: 'Price above all major MAs' }
            ],
            news_sentiment: [
              { headline: 'Tech Sector Shows Strong Growth', source: 'Financial Times', sentiment: 0.8, impact: 'High' }
            ]
          }
        },
        ticker: 'AAPL',
        aggregate_performance: {
          return: 15.8,
          sharpe_ratio: 1.95,
          max_drawdown: -8.2,
          win_rate: 68.5,
          trades_count: 35
        }
      },
      {
        id: 2,
        strategy: {
          id: 'ml_strategy_2',
          name: 'Breakout Momentum v20250417',
          template: 'breakout_momentum',
          confidence_score: 0.78,
          reasoning: {
            summary: 'Selected based on increasing volatility and volume patterns',
            political_factors: ['Neutral political environment'],
            social_factors: ['Neutral social sentiment'],
            economic_factors: ['Favorable financial news detected'],
            technical_indicators: [
              { name: 'Volume', signal: 'bullish', description: 'Increasing volume on up days' }
            ]
          }
        },
        ticker: 'MSFT',
        aggregate_performance: {
          return: 12.3,
          sharpe_ratio: 1.65,
          max_drawdown: -10.5,
          win_rate: 62.1,
          trades_count: 28
        }
      }
    ];
    
    // Mock losing strategies
    const losing = [
      {
        id: 3,
        strategy: {
          id: 'ml_strategy_3',
          name: 'RSI Reversal v20250417',
          template: 'rsi_reversal',
          confidence_score: 0.52,
          reasoning: {
            summary: 'Selected for mean reversion potential in sideways market',
            political_factors: ['Some regulatory concerns detected'],
            social_factors: ['Minor social concerns detected'],
            economic_factors: ['Economic uncertainty in sector'],
            technical_indicators: [
              { name: 'RSI', signal: 'neutral', description: 'RSI in mid-range' }
            ]
          }
        },
        ticker: 'META',
        aggregate_performance: {
          return: -4.2,
          sharpe_ratio: 0.45,
          max_drawdown: -15.8,
          win_rate: 42.3,
          trades_count: 31
        }
      }
    ];
    
    setTopWinningStrategies(winning);
    setTopLosingStrategies(losing);
    
    // Mock collaborative strategies
    setCollaborativeWinningStrategies([
      {
        id: 101,
        strategy: {
          id: 'user_strategy_1',
          name: 'Custom MA Crossover',
          template: 'moving_average_crossover',
          confidence_score: 0.72
        },
        ticker: 'SPY',
        aggregate_performance: {
          return: 8.5,
          sharpe_ratio: 1.42,
          max_drawdown: -7.8,
          win_rate: 58.0,
          trades_count: 22
        }
      }
    ]);
    
    setCollaborativeLosingStrategies([
      {
        id: 102,
        strategy: {
          id: 'user_strategy_2',
          name: 'Custom MACD Strategy',
          template: 'custom_strategy',
          confidence_score: 0.45
        },
        ticker: 'AMZN',
        aggregate_performance: {
          return: -2.8,
          sharpe_ratio: 0.35,
          max_drawdown: -12.1,
          win_rate: 40.0,
          trades_count: 18
        }
      }
    ]);
  };

  // Handle view details for a strategy
  const handleViewDetails = (strategyId) => {
    const allStrategies = [
      ...topWinningStrategies, 
      ...topLosingStrategies,
      ...collaborativeWinningStrategies,
      ...collaborativeLosingStrategies
    ];
    
    const strategy = allStrategies.find(s => s.id === strategyId);
    setSelectedStrategy(strategy);
  };

  // Filter strategies based on filter parameters
  const filterStrategies = (strategies) => {
    return strategies.filter(s => {
      // Add filtering logic here if needed
      return true;
    });
  };

  // Component for strategy cards
  const StrategyCard = ({ 
    strategy, 
    performance,
    ticker,
    isWinning, 
    isML = true, 
    isTop = false, 
    onViewDetails 
  }) => {
    const textColorClass = isWinning ? 'text-green-600' : 'text-red-600';
    const bgColorClass = isML ? 'bg-purple-50' : 'bg-white';
    const borderColorClass = isWinning ? 'border-green-200' : 'border-red-200';
    
    return (
      <div className={`rounded-lg shadow-md ${bgColorClass} border ${borderColorClass} overflow-hidden mb-4 transition-all hover:shadow-lg`}>
        {isTop && (
          <div className={`px-3 py-1 text-xs font-medium bg-${isWinning ? 'green' : 'red'}-100 text-${isWinning ? 'green' : 'red'}-800 flex items-center`}>
            <Award className="w-3 h-3 mr-1" />
            <span>Top {isWinning ? 'Performing' : 'Underperforming'} ML Strategy</span>
          </div>
        )}
        
        <div className="p-4">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center">
                {isML && <BrainCircuit className="w-4 h-4 text-purple-600 mr-2" />}
                {!isML && <Users className="w-4 h-4 text-blue-600 mr-2" />}
                <h3 className="font-bold text-gray-800">{strategy.name}</h3>
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {ticker} • {performance.trades_count} trades • {performance.win_rate.toFixed(1)}% win rate
              </div>
            </div>
            
            <div className={`text-lg font-bold ${textColorClass} flex items-center`}>
              {isWinning ? (
                <>
                  <ArrowUpRight className="w-4 h-4 mr-1" />
                  +{performance.return.toFixed(1)}%
                </>
              ) : (
                <>
                  <ArrowDownRight className="w-4 h-4 mr-1" />
                  {performance.return.toFixed(1)}%
                </>
              )}
            </div>
          </div>
          
          {/* Performance Metrics */}
          <div className="mt-3 grid grid-cols-3 gap-2">
            <div className="bg-gray-50 rounded p-2">
              <div className="text-xs text-gray-500">Sharpe</div>
              <div className={`font-medium ${performance.sharpe_ratio > 1 ? 'text-green-600' : 'text-gray-700'}`}>
                {performance.sharpe_ratio.toFixed(2)}
              </div>
              <div className="w-full bg-gray-200 h-1 rounded-full mt-1">
                <div 
                  className="bg-blue-500 h-1 rounded-full" 
                  style={{ width: `${Math.min(performance.sharpe_ratio / 3 * 100, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded p-2">
              <div className="text-xs text-gray-500">Win Rate</div>
              <div className={`font-medium ${performance.win_rate > 50 ? 'text-green-600' : 'text-red-600'}`}>
                {performance.win_rate.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 h-1 rounded-full mt-1">
                <div 
                  className={`${performance.win_rate > 50 ? 'bg-green-500' : 'bg-red-500'} h-1 rounded-full`} 
                  style={{ width: `${performance.win_rate}%` }}
                ></div>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded p-2">
              <div className="text-xs text-gray-500">
                {isML ? 'ML Confidence' : 'Drawdown'}
              </div>
              <div className="font-medium">
                {isML 
                  ? `${(strategy.confidence_score * 100).toFixed(0)}%`
                  : `${performance.max_drawdown.toFixed(1)}%`
                }
              </div>
              <div className="w-full bg-gray-200 h-1 rounded-full mt-1">
                <div 
                  className={`${isML ? 'bg-purple-500' : 'bg-red-500'} h-1 rounded-full`} 
                  style={{ 
                    width: isML 
                      ? `${strategy.confidence_score * 100}%` 
                      : `${Math.min(Math.abs(performance.max_drawdown) / 20 * 100, 100)}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-2 mt-3">
            <button 
              onClick={() => onViewDetails(strategy.id)}
              className="flex-1 text-xs bg-blue-50 text-blue-700 px-2 py-2 rounded flex items-center justify-center hover:bg-blue-100 transition-colors"
            >
              <BarChart2 className="w-3 h-3 mr-1" />
              View Details
            </button>
            
            {isML && (
              <button className="flex-1 text-xs bg-purple-50 text-purple-700 px-2 py-2 rounded flex items-center justify-center hover:bg-purple-100 transition-colors">
                <Zap className="w-3 h-3 mr-1" />
                Show ML Reasoning
              </button>
            )}
            
            {!isML && (
              <button className="flex-1 text-xs bg-green-50 text-green-700 px-2 py-2 rounded flex items-center justify-center hover:bg-green-100 transition-colors">
                <Activity className="w-3 h-3 mr-1" />
                Edit Strategy
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // ML Reasoning panel
  const MLReasoningPanel = ({ strategy }) => {
    if (!strategy || !strategy.strategy.reasoning) return null;
    
    const reasoning = strategy.strategy.reasoning;
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-4 border border-purple-200 mb-4">
        <h3 className="text-lg font-bold text-gray-800 mb-3">ML Strategy Reasoning</h3>
        
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700">Strategy Formation</h4>
          <p className="text-sm text-gray-600 mt-1">{reasoning.summary}</p>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700">Political Factors</h4>
            <ul className="mt-1 text-sm space-y-1">
              {reasoning.political_factors.map((factor, index) => (
                <li key={index} className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></div>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700">Social Factors</h4>
            <ul className="mt-1 text-sm space-y-1">
              {reasoning.social_factors.map((factor, index) => (
                <li key={index} className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-green-500 mt-1.5 mr-2 flex-shrink-0"></div>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700">Economic Factors</h4>
            <ul className="mt-1 text-sm space-y-1">
              {reasoning.economic_factors.map((factor, index) => (
                <li key={index} className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 mt-1.5 mr-2 flex-shrink-0"></div>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        {reasoning.technical_indicators && reasoning.technical_indicators.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700">Technical Indicators</h4>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {reasoning.technical_indicators.map((indicator, index) => (
                <div key={index} className="bg-gray-50 rounded p-2 text-xs">
                  <div className="font-medium">{indicator.name}</div>
                  <div className="text-gray-600">{indicator.description}</div>
                  <div className={indicator.signal === 'bullish' ? 'text-green-600' : indicator.signal === 'bearish' ? 'text-red-600' : 'text-gray-600'}>
                    Signal: {indicator.signal}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {reasoning.news_sentiment && reasoning.news_sentiment.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700">News Sentiment Insights</h4>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {reasoning.news_sentiment.map((news, index) => (
                <div key={index} className="bg-gray-50 rounded p-2 text-xs">
                  <div className="font-medium">{news.headline}</div>
                  <div className="text-gray-600">{news.source}</div>
                  <div className="flex justify-between">
                    <span>Impact: {news.impact}</span>
                    <span className={news.sentiment > 0 ? 'text-green-600' : 'text-red-600'}>
                      Sentiment: {news.sentiment > 0 ? 'Positive' : 'Negative'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-gray-50 p-4">
      {/* Header with filters */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <h2 className="text-2xl font-bold text-gray-800">Autonomous ML Backtesting</h2>
          <div className="bg-purple-100 text-purple-800 text-xs font-medium px-2.5 py-0.5 rounded ml-2">AI-Powered</div>
        </div>
        
        <div className="flex space-x-3">
          <select 
            className="bg-white border border-gray-300 text-gray-700 rounded px-3 py-2 text-sm"
            value={filterParams.sector}
            onChange={(e) => setFilterParams({...filterParams, sector: e.target.value})}
          >
            <option value="all">All Sectors</option>
            <option value="technology">Technology</option>
            <option value="finance">Finance</option>
            <option value="healthcare">Healthcare</option>
            <option value="consumer">Consumer</option>
          </select>
          
          <select 
            className="bg-white border border-gray-300 text-gray-700 rounded px-3 py-2 text-sm"
            value={filterParams.marketCondition}
            onChange={(e) => setFilterParams({...filterParams, marketCondition: e.target.value})}
          >
            <option value="all">All Market Conditions</option>
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
            <option value="volatile">Volatile</option>
            <option value="sideways">Sideways</option>
          </select>
          
          <select 
            className="bg-white border border-gray-300 text-gray-700 rounded px-3 py-2 text-sm"
            value={filterParams.timeRange}
            onChange={(e) => setFilterParams({...filterParams, timeRange: e.target.value})}
          >
            <option value="1m">1 Month</option>
            <option value="3m">3 Months</option>
            <option value="6m">6 Months</option>
            <option value="1y">1 Year</option>
            <option value="2y">2 Years</option>
            <option value="5y">5 Years</option>
          </select>
          
          <button 
            onClick={runAutonomousBacktests}
            disabled={isRunningTests}
            className={`flex items-center ${isRunningTests ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'} text-white px-4 py-2 rounded-md transition-colors`}
          >
            {isRunningTests ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Running ML Tests...
              </>
            ) : (
              <>
                <BrainCircuit className="w-4 h-4 mr-2" />
                Run ML Tests
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* ML Learning Status */}
      <div className="bg-gradient-to-r from-purple-100 to-blue-50 rounded-lg p-4 mb-6 border border-purple-100">
        <div className="flex items-start">
          <BrainCircuit className="w-6 h-6 text-purple-600 mr-3 mt-1 flex-shrink-0" />
          <div className="flex-grow">
            <h3 className="font-medium text-gray-800">ML Learning Status</h3>
            <p className="text-sm text-gray-600 mb-2">
              Currently analyzing {filterParams.timeRange === 'all' ? 'all historical' : filterParams.timeRange} market data
              {filterParams.sector !== 'all' ? ` for the ${filterParams.sector} sector` : ''}
              {filterParams.marketCondition !== 'all' ? ` during ${filterParams.marketCondition.toLowerCase()} conditions` : ''}.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
              {mlStatus.dataSourcesActive.map((source, index) => (
                <div key={index} className="flex items-center bg-white rounded-md p-2 shadow-sm">
                  <div className={`w-2 h-2 rounded-full ${source.active ? 'bg-green-500' : 'bg-yellow-500'} mr-2`}></div>
                  {source.type === 'historical' && <Database className="w-4 h-4 text-blue-600 mr-2" />}
                  {source.type === 'news' && <Newspaper className="w-4 h-4 text-blue-600 mr-2" />}
                  {source.type === 'indicators' && <Activity className="w-4 h-4 text-purple-600 mr-2" />}
                  <span className="text-xs">{source.name} {source.status}</span>
                </div>
              ))}
            </div>
            
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-700">ML Insights</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                {mlStatus.insights.map((insight, index) => (
                  <div key={index} className="bg-white rounded p-2 text-xs border border-purple-100">
                    <div className="flex items-center">
                      <Lightbulb className="w-3 h-3 text-yellow-600 mr-1" />
                      <div className="font-medium">{insight.title}</div>
                    </div>
                    <div className="text-gray-600 mt-1">{insight.description}</div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-3 flex justify-between items-center">
              <div className="text-xs text-gray-500">
                ML Model: v{mlStatus.modelVersion || '1.0'}
              </div>
              <div className="text-xs text-gray-500">
                Last updated: {mlStatus.lastTrained ? new Date(mlStatus.lastTrained).toLocaleString() : 'Never'}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Selected strategy details */}
      {selectedStrategy && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <BrainCircuit className="w-5 h-5 text-purple-600 mr-2" />
            Strategy Details
            <button 
              onClick={() => setSelectedStrategy(null)}
              className="ml-auto text-xs text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </h3>
          <MLReasoningPanel strategy={selectedStrategy} />
        </div>
      )}
      
      {/* Two-column layout for strategies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Winning Strategies Column */}
        <div>
          <div className="flex items-center mb-3">
            <ArrowUpRight className="w-5 h-5 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Winning Strategies</h3>
            <div className="ml-2 bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">
              {filterStrategies(topWinningStrategies).length + filterStrategies(collaborativeWinningStrategies).length}
            </div>
          </div>
          
          {/* Top ML-Generated Winning Strategies */}
          <div className="mb-6">
            <div className="flex items-center mb-2">
              <BrainCircuit className="w-4 h-4 text-purple-600 mr-1" />
              <h4 className="text-sm font-medium text-gray-700">Top ML-Generated</h4>
            </div>
            
            <div className="space-y-4">
              {filterStrategies(topWinningStrategies).map(strategy => (
                <StrategyCard 
                  key={strategy.id} 
                  strategy={strategy.strategy} 
                  performance={strategy.aggregate_performance}
                  ticker={strategy.ticker}
                  isWinning={true} 
                  isML={true} 
                  isTop={true}
                  onViewDetails={handleViewDetails}
                />
              ))}
              
              {filterStrategies(topWinningStrategies).length === 0 && (
                <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500 border border-gray-200">
                  No ML-generated winning strategies found. Run ML tests to generate strategies.
                </div>
              )}
            </div>
          </div>
          
          {/* Collaborative Winning Strategies */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Users className="w-4 h-4 text-blue-600 mr-1" />
                <h4 className="text-sm font-medium text-gray-700">Your Collaborative Strategies</h4>
              </div>
              
              <button className="text-xs flex items-center text-blue-600 hover:text-blue-800">
                <PlusCircle className="w-3 h-3 mr-1" />
                Create New
              </button>
            </div>
            
            <div className="space-y-4">
              {filterStrategies(collaborativeWinningStrategies).map(strategy => (
                <StrategyCard 
                  key={strategy.id} 
                  strategy={strategy.strategy}
                  performance={strategy.aggregate_performance}
                  ticker={strategy.ticker}
                  isWinning={true} 
                  isML={false}
                  onViewDetails={handleViewDetails}
                />
              ))}
              
              {filterStrategies(collaborativeWinningStrategies).length === 0 && (
                <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500 border border-gray-200">
                  No collaborative winning strategies yet. Create one or use ML suggestions to get started.
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Losing Strategies Column */}
        <div>
          <div className="flex items-center mb-3">
            <ArrowDownRight className="w-5 h-5 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Losing Strategies</h3>
            <div className="ml-2 bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">
              {filterStrategies(topLosingStrategies).length + filterStrategies(collaborativeLosingStrategies).length}
            </div>
          </div>
          
          {/* Top ML-Generated Losing Strategies */}
          <div className="mb-6">
            <div className="flex items-center mb-2">
              <BrainCircuit className="w-4 h-4 text-purple-600 mr-1" />
              <h4 className="text-sm font-medium text-gray-700">Top ML-Generated</h4>
            </div>
            
            <div className="space-y-4">
              {filterStrategies(topLosingStrategies).map(strategy => (
                <StrategyCard 
                  key={strategy.id} 
                  strategy={strategy.strategy}
                  performance={strategy.aggregate_performance}
                  ticker={strategy.ticker}
                  isWinning={false} 
                  isML={true} 
                  isTop={true}
                  onViewDetails={handleViewDetails}
                />
              ))}
              
              {filterStrategies(topLosingStrategies).length === 0 && (
                <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500 border border-gray-200">
                  No ML-generated losing strategies found. Run ML tests to generate strategies.
                </div>
              )}
            </div>
          </div>
          
          {/* Collaborative Losing Strategies */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Users className="w-4 h-4 text-blue-600 mr-1" />
                <h4 className="text-sm font-medium text-gray-700">Your Collaborative Strategies</h4>
              </div>
            </div>
            
            <div className="space-y-4">
              {filterStrategies(collaborativeLosingStrategies).map(strategy => (
                <StrategyCard 
                  key={strategy.id} 
                  strategy={strategy.strategy}
                  performance={strategy.aggregate_performance}
                  ticker={strategy.ticker}
                  isWinning={false} 
                  isML={false}
                  onViewDetails={handleViewDetails}
                />
              ))}
              
              {filterStrategies(collaborativeLosingStrategies).length === 0 && (
                <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500 border border-gray-200">
                  No collaborative losing strategies. Great job maintaining quality strategies!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BacktestTab; 