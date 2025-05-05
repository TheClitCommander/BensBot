import React, { useState } from 'react';
import LogMonitor from './LogMonitor';
import PerformanceStats from './PerformanceStats';
import SystemConfig from './SystemConfig';

const Developer = () => {
  const [activeDevTab, setActiveDevTab] = useState('System Monitor');

  // Tabs available in the developer section
  const devTabs = [
    'System Monitor',
    'Performance Stats',
    'System Config'
  ];

  // Render the active dev component based on the selected tab
  const renderActiveDevComponent = () => {
    switch (activeDevTab) {
      case 'System Monitor':
        return <LogMonitor />;
      case 'Performance Stats':
        return <PerformanceStats />;
      case 'System Config':
        return <SystemConfig />;
      default:
        return <LogMonitor />;
    }
  };

  return (
    <div>
      <h1>Developer Tools</h1>
      
      <div style={{ 
        display: 'flex', 
        borderBottom: '1px solid #333',
        marginBottom: '24px'
      }}>
        {devTabs.map((tab) => (
          <div
            key={tab}
            onClick={() => setActiveDevTab(tab)}
            style={{
              padding: '12px 24px',
              cursor: 'pointer',
              borderBottom: activeDevTab === tab 
                ? '2px solid #4F8BFF' 
                : '2px solid transparent',
              color: activeDevTab === tab 
                ? '#4F8BFF' 
                : '#9e9e9e',
              fontWeight: activeDevTab === tab 
                ? '500' 
                : 'normal'
            }}
          >
            {tab}
          </div>
        ))}
      </div>
      
      {renderActiveDevComponent()}
    </div>
  );
};

export default Developer;
