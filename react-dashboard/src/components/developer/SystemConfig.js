import React, { useState } from 'react';

const SystemConfig = () => {
  // Mock data for system configuration
  const [configData, setConfigData] = useState({
    generalSettings: {
      systemName: 'BensBot Trading Platform',
      environment: 'Production',
      logLevel: 'info',
      autoStartEnabled: true,
      maintenanceMode: false,
      dataRetentionDays: 90
    },
    apiKeys: {
      alphaVantage: '********************ABCD',
      tradingView: '********************EFGH',
      newsAPI: '********************IJKL',
      openAI: '********************MNOP',
      iexCloud: '********************QRST'
    },
    connections: {
      brokers: [
        { name: 'Interactive Brokers', enabled: true, environment: 'Live', status: 'Connected' },
        { name: 'Alpaca', enabled: true, environment: 'Paper', status: 'Connected' },
        { name: 'Binance', enabled: true, environment: 'Live', status: 'Connected' },
        { name: 'Coinbase', enabled: false, environment: 'Paper', status: 'Disconnected' },
        { name: 'TD Ameritrade', enabled: false, environment: 'Paper', status: 'Disconnected' }
      ],
      dataProviders: [
        { name: 'Alpha Vantage', enabled: true, status: 'Connected', rateLimit: '500 requests/day' },
        { name: 'IEX Cloud', enabled: true, status: 'Connected', rateLimit: '50,000 credits/month' },
        { name: 'Trading View', enabled: true, status: 'Connected', rateLimit: 'Premium' },
        { name: 'Polygon.io', enabled: false, status: 'Disconnected', rateLimit: 'N/A' }
      ]
    },
    systemLimits: {
      maxActiveStrategies: 10,
      maxBacktestsPerDay: 50,
      maxParallelBacktests: 3,
      maxSymbolsPerStrategy: 20,
      maxHistoricalDataYears: 10,
      memoryLimit: 16, // GB
      diskSpaceLimit: 100 // GB
    },
    aiSettings: {
      openAIModel: 'gpt-4',
      sentimentAnalysisEnabled: true,
      predictiveAnalyticsEnabled: true,
      autoStrategyGenerationEnabled: true,
      minervaEnabled: true,
      crossAssetInsightsEnabled: true
    }
  });

  // Handle toggle change
  const handleToggleChange = (section, key) => {
    setConfigData({
      ...configData,
      [section]: {
        ...configData[section],
        [key]: !configData[section][key]
      }
    });
  };

  // Handle input change
  const handleInputChange = (section, key, value) => {
    setConfigData({
      ...configData,
      [section]: {
        ...configData[section],
        [key]: value
      }
    });
  };

  // Handle broker toggle
  const handleBrokerToggle = (index) => {
    const updatedBrokers = [...configData.connections.brokers];
    updatedBrokers[index] = {
      ...updatedBrokers[index],
      enabled: !updatedBrokers[index].enabled,
      status: !updatedBrokers[index].enabled ? 'Connected' : 'Disconnected'
    };
    
    setConfigData({
      ...configData,
      connections: {
        ...configData.connections,
        brokers: updatedBrokers
      }
    });
  };

  // Handle data provider toggle
  const handleDataProviderToggle = (index) => {
    const updatedDataProviders = [...configData.connections.dataProviders];
    updatedDataProviders[index] = {
      ...updatedDataProviders[index],
      enabled: !updatedDataProviders[index].enabled,
      status: !updatedDataProviders[index].enabled ? 'Connected' : 'Disconnected'
    };
    
    setConfigData({
      ...configData,
      connections: {
        ...configData.connections,
        dataProviders: updatedDataProviders
      }
    });
  };

  return (
    <div className="dashboard-grid">
      <div className="card">
        <h2 className="card-header">System Configuration</h2>
        <div className="card-content">
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>General Settings</h3>
              <button
                style={{
                  backgroundColor: '#4F8BFF',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Save Changes
              </button>
            </div>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '16px',
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px'
            }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                  System Name
                </label>
                <input
                  type="text"
                  value={configData.generalSettings.systemName}
                  onChange={(e) => handleInputChange('generalSettings', 'systemName', e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                  Environment
                </label>
                <select
                  value={configData.generalSettings.environment}
                  onChange={(e) => handleInputChange('generalSettings', 'environment', e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                >
                  <option value="Development">Development</option>
                  <option value="Staging">Staging</option>
                  <option value="Production">Production</option>
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                  Log Level
                </label>
                <select
                  value={configData.generalSettings.logLevel}
                  onChange={(e) => handleInputChange('generalSettings', 'logLevel', e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                >
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                  Data Retention (days)
                </label>
                <input
                  type="number"
                  value={configData.generalSettings.dataRetentionDays}
                  onChange={(e) => handleInputChange('generalSettings', 'dataRetentionDays', parseInt(e.target.value))}
                  style={{
                    width: '100%',
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div>
                  <span>Auto-start Enabled</span>
                </div>
                <div 
                  style={{ 
                    width: '40px', 
                    height: '20px', 
                    backgroundColor: configData.generalSettings.autoStartEnabled ? '#4CAF50' : '#333',
                    borderRadius: '10px',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'background-color 0.3s'
                  }}
                  onClick={() => handleToggleChange('generalSettings', 'autoStartEnabled')}
                >
                  <div 
                    style={{
                      width: '16px',
                      height: '16px',
                      backgroundColor: 'white',
                      borderRadius: '50%',
                      position: 'absolute',
                      top: '2px',
                      left: configData.generalSettings.autoStartEnabled ? '22px' : '2px',
                      transition: 'left 0.3s'
                    }}
                  />
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div>
                  <span>Maintenance Mode</span>
                </div>
                <div 
                  style={{ 
                    width: '40px', 
                    height: '20px', 
                    backgroundColor: configData.generalSettings.maintenanceMode ? '#F44336' : '#333',
                    borderRadius: '10px',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'background-color 0.3s'
                  }}
                  onClick={() => handleToggleChange('generalSettings', 'maintenanceMode')}
                >
                  <div 
                    style={{
                      width: '16px',
                      height: '16px',
                      backgroundColor: 'white',
                      borderRadius: '50%',
                      position: 'absolute',
                      top: '2px',
                      left: configData.generalSettings.maintenanceMode ? '22px' : '2px',
                      transition: 'left 0.3s'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>API Keys</h3>
            <div style={{ 
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px'
            }}>
              {Object.entries(configData.apiKeys).map(([provider, key]) => (
                <div 
                  key={provider}
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '16px',
                    marginBottom: '12px'
                  }}
                >
                  <div style={{ width: '150px', fontWeight: '500' }}>
                    {provider.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                  </div>
                  <div style={{ flex: 1, position: 'relative' }}>
                    <input
                      type="password"
                      value={key}
                      onChange={(e) => handleInputChange('apiKeys', provider, e.target.value)}
                      style={{
                        width: '100%',
                        backgroundColor: '#333',
                        border: 'none',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        color: 'white'
                      }}
                    />
                    <button
                      style={{
                        position: 'absolute',
                        right: '8px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#9e9e9e',
                        cursor: 'pointer'
                      }}
                    >
                      <span className="material-icons" style={{ fontSize: '18px' }}>visibility</span>
                    </button>
                  </div>
                  <button
                    style={{
                      backgroundColor: 'transparent',
                      border: '1px solid #9e9e9e',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      color: '#9e9e9e',
                      cursor: 'pointer'
                    }}
                  >
                    Verify
                  </button>
                </div>
              ))}
              <button
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #4F8BFF',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  color: '#4F8BFF',
                  cursor: 'pointer',
                  marginTop: '8px'
                }}
              >
                <span className="material-icons" style={{ fontSize: '18px', verticalAlign: 'middle', marginRight: '4px' }}>add</span>
                Add New API Key
              </button>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>Broker Connections</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Broker</th>
                    <th>Environment</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {configData.connections.brokers.map((broker, index) => (
                    <tr key={index}>
                      <td>{broker.name}</td>
                      <td>{broker.environment}</td>
                      <td>
                        <span className={`badge ${broker.status === 'Connected' ? 'success' : 'danger'}`}>
                          {broker.status}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <div 
                            style={{ 
                              width: '40px', 
                              height: '20px', 
                              backgroundColor: broker.enabled ? '#4CAF50' : '#333',
                              borderRadius: '10px',
                              position: 'relative',
                              cursor: 'pointer',
                              transition: 'background-color 0.3s'
                            }}
                            onClick={() => handleBrokerToggle(index)}
                          >
                            <div 
                              style={{
                                width: '16px',
                                height: '16px',
                                backgroundColor: 'white',
                                borderRadius: '50%',
                                position: 'absolute',
                                top: '2px',
                                left: broker.enabled ? '22px' : '2px',
                                transition: 'left 0.3s'
                              }}
                            />
                          </div>
                          <button
                            style={{
                              backgroundColor: 'transparent',
                              border: 'none',
                              color: '#9e9e9e',
                              cursor: 'pointer'
                            }}
                          >
                            <span className="material-icons" style={{ fontSize: '18px' }}>settings</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>Data Provider Connections</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Rate Limit</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {configData.connections.dataProviders.map((provider, index) => (
                    <tr key={index}>
                      <td>{provider.name}</td>
                      <td>{provider.rateLimit}</td>
                      <td>
                        <span className={`badge ${provider.status === 'Connected' ? 'success' : 'danger'}`}>
                          {provider.status}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <div 
                            style={{ 
                              width: '40px', 
                              height: '20px', 
                              backgroundColor: provider.enabled ? '#4CAF50' : '#333',
                              borderRadius: '10px',
                              position: 'relative',
                              cursor: 'pointer',
                              transition: 'background-color 0.3s'
                            }}
                            onClick={() => handleDataProviderToggle(index)}
                          >
                            <div 
                              style={{
                                width: '16px',
                                height: '16px',
                                backgroundColor: 'white',
                                borderRadius: '50%',
                                position: 'absolute',
                                top: '2px',
                                left: provider.enabled ? '22px' : '2px',
                                transition: 'left 0.3s'
                              }}
                            />
                          </div>
                          <button
                            style={{
                              backgroundColor: 'transparent',
                              border: 'none',
                              color: '#9e9e9e',
                              cursor: 'pointer'
                            }}
                          >
                            <span className="material-icons" style={{ fontSize: '18px' }}>settings</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>System Limits</h3>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px'
            }}>
              {Object.entries(configData.systemLimits).map(([limit, value]) => (
                <div key={limit}>
                  <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                    {limit.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()).replace('Max', 'Max ')}
                  </label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => handleInputChange('systemLimits', limit, parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      backgroundColor: '#333',
                      border: 'none',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      color: 'white'
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ marginBottom: '16px' }}>AI Settings</h3>
            <div style={{ 
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px'
            }}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                  OpenAI Model
                </label>
                <select
                  value={configData.aiSettings.openAIModel}
                  onChange={(e) => handleInputChange('aiSettings', 'openAIModel', e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: '#333',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                {Object.entries(configData.aiSettings)
                  .filter(([key]) => key !== 'openAIModel')
                  .map(([feature, enabled]) => (
                    <div key={feature} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div>
                        <span>{feature.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()).replace('Enabled', '')}</span>
                      </div>
                      <div 
                        style={{ 
                          width: '40px', 
                          height: '20px', 
                          backgroundColor: enabled ? '#4CAF50' : '#333',
                          borderRadius: '10px',
                          position: 'relative',
                          cursor: 'pointer',
                          transition: 'background-color 0.3s'
                        }}
                        onClick={() => handleToggleChange('aiSettings', feature)}
                      >
                        <div 
                          style={{
                            width: '16px',
                            height: '16px',
                            backgroundColor: 'white',
                            borderRadius: '50%',
                            position: 'absolute',
                            top: '2px',
                            left: enabled ? '22px' : '2px',
                            transition: 'left 0.3s'
                          }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #F44336',
                padding: '8px 16px',
                borderRadius: '4px',
                color: '#F44336',
                cursor: 'pointer'
              }}
            >
              Reset to Defaults
            </button>
            <div>
              <button
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #9e9e9e',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  color: '#9e9e9e',
                  cursor: 'pointer',
                  marginRight: '12px'
                }}
              >
                Cancel
              </button>
              <button
                style={{
                  backgroundColor: '#4F8BFF',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Save All Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemConfig;
