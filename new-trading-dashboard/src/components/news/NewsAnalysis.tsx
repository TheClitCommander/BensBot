import React, { useState } from 'react';
import MarketOverview from './MarketOverview';
import SymbolNews from './SymbolNews';
import EconomicCalendar from './EconomicCalendar';
import PortfolioImpact from './PortfolioImpact';

type NewsTabType = 'Market Overview' | 'Symbol News' | 'Economic Calendar' | 'Portfolio Impact';

const NewsAnalysis: React.FC = () => {
  const [activeNewsTab, setActiveNewsTab] = useState<NewsTabType>('Market Overview');

  // Tabs available in the news section
  const newsTabs: NewsTabType[] = [
    'Market Overview',
    'Symbol News',
    'Economic Calendar',
    'Portfolio Impact'
  ];

  // Render the active news component based on the selected tab
  const renderActiveNewsComponent = () => {
    switch (activeNewsTab) {
      case 'Market Overview':
        return <MarketOverview />;
      case 'Symbol News':
        return <SymbolNews />;
      case 'Economic Calendar':
        return <EconomicCalendar />;
      case 'Portfolio Impact':
        return <PortfolioImpact />;
      default:
        return <MarketOverview />;
    }
  };

  return (
    <div>
      <h1>News & Market Analysis</h1>
      
      <div style={{ 
        display: 'flex', 
        borderBottom: '1px solid #333',
        marginBottom: '24px'
      }}>
        {newsTabs.map((tab) => (
          <div
            key={tab}
            onClick={() => setActiveNewsTab(tab)}
            style={{
              padding: '12px 24px',
              cursor: 'pointer',
              borderBottom: activeNewsTab === tab 
                ? '2px solid #4F8BFF' 
                : '2px solid transparent',
              color: activeNewsTab === tab 
                ? '#4F8BFF' 
                : '#9e9e9e',
              fontWeight: activeNewsTab === tab 
                ? '500' 
                : 'normal'
            }}
          >
            {tab}
          </div>
        ))}
      </div>
      
      {renderActiveNewsComponent()}
    </div>
  );
};

export default NewsAnalysis;
