import React from 'react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  // Navigation items
  const navItems = [
    { name: 'Dashboard', icon: 'dashboard' },
    { name: 'Backtester', icon: 'assessment' },
    { name: 'News/Predictions', icon: 'trending_up' },
    { name: 'Developer', icon: 'code' },
    { name: 'Settings', icon: 'settings' },
  ];

  return (
    <div className="sidebar">
      <div className="logo-container">
        <div className="logo">
          <img 
            src="https://via.placeholder.com/150x80?text=BensBot" 
            alt="BensBot Logo" 
            style={{ width: '100%' }}
          />
        </div>
        <div className="logo-text">BensBot Trading</div>
      </div>
      
      <nav>
        {navItems.map((item) => (
          <div
            key={item.name}
            className={`nav-link ${activeTab === item.name ? 'active' : ''}`}
            onClick={() => setActiveTab(item.name)}
          >
            <span className="material-icons" style={{ marginRight: '8px', verticalAlign: 'middle' }}>
              {item.icon}
            </span>
            {item.name}
          </div>
        ))}
      </nav>
      
      <div style={{ marginTop: 'auto', padding: '1rem 0' }}>
        <div style={{ fontSize: '0.8rem', color: '#9e9e9e', marginBottom: '1rem' }}>
          © 2025 BensBot Trading Platform
        </div>
        <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>
          Version 2.3.4
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
