import React, { useState } from 'react';

// Define types for the configuration data
interface GeneralSettings {
  systemName: string;
  environment: string;
  logLevel: string;
  autoStartEnabled: boolean;
  maintenanceMode: boolean;
  dataRetentionDays: number;
}

interface ApiKeys {
  alphaVantage: string;
  tradingView: string;
  newsAPI: string;
  openAI: string;
  iexCloud: string;
}

interface Broker {
  name: string;
  enabled: boolean;
  environment: 'Live' | 'Paper';
  status: 'Connected' | 'Disconnected';
}

interface DataProvider {
  name: string;
  enabled: boolean;
  status: 'Connected' | 'Disconnected';
  rateLimit: string;
}

interface SystemLimits {
  maxActiveStrategies: number;
  maxBacktestsPerDay: number;
  maxParallelBacktests: number;
  maxSymbolsPerStrategy: number;
  maxHistoricalDataYears: number;
  memoryLimit: number; // GB
  diskSpaceLimit: number; // GB
}

interface AiSettings {
  openAIModel: string;
  sentimentAnalysisEnabled: boolean;
  predictiveAnalyticsEnabled: boolean;
  autoStrategyGenerationEnabled: boolean;
  minervaEnabled: boolean;
  crossAssetInsightsEnabled: boolean;
}

interface Connections {
  brokers: Broker[];
  dataProviders: DataProvider[];
}

interface ConfigData {
  generalSettings: GeneralSettings;
  apiKeys: ApiKeys;
  connections: Connections;
  systemLimits: SystemLimits;
  aiSettings: AiSettings;
}

const SystemConfig: React.FC = () => {
  // Mock data for system configuration
  // In production would load from config file/API
  const [configData, setConfigData] = useState<ConfigData>({
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
  const handleToggleChange = (section: keyof ConfigData, key: string) => {
    setConfigData({
      ...configData,
      [section]: {
        ...configData[section as keyof ConfigData],
        [key]: !configData[section as keyof ConfigData][key as keyof typeof configData[typeof section]]
      }
    });
  };

  // Handle input change
  const handleInputChange = (section: keyof ConfigData, key: string, value: string | number | boolean) => {
    setConfigData({
      ...configData,
      [section]: {
        ...configData[section as keyof ConfigData],
        [key]: value
      }
    });
  };

  // Handle broker toggle
  const handleBrokerToggle = (index: number) => {
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
  const handleDataProviderToggle = (index: number) => {
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
                Restart System
              </button>
            </div>
            
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '16px'
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
                    Data Retention (Days)
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
              </div>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '16px',
                marginTop: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div>
                    <span>Auto Start Enabled</span>
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
            
            <h3>API Keys</h3>
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '16px'
              }}>
                {Object.entries(configData.apiKeys).map(([apiName, apiKey]) => (
                  <div key={apiName}>
                    <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                      {apiName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => handleInputChange('apiKeys', apiName, e.target.value)}
                        style={{
                          flex: 1,
                          backgroundColor: '#333',
                          border: 'none',
                          padding: '8px 12px',
                          borderRadius: '4px',
                          color: 'white'
                        }}
                      />
                      <button
                        style={{
                          backgroundColor: 'transparent',
                          border: '1px solid #9e9e9e',
                          borderRadius: '4px',
                          color: '#9e9e9e',
                          cursor: 'pointer',
                          padding: '0 8px'
                        }}
                      >
                        Show
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '16px', textAlign: 'right' }}>
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
                  Verify All Keys
                </button>
              </div>
            </div>
            
            <h3>Broker Connections</h3>
            <div style={{ 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px',
              overflow: 'hidden'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#333' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Broker</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Environment</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Status</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {configData.connections.brokers.map((broker, index) => (
                    <tr 
                      key={broker.name}
                      style={{ 
                        borderBottom: index === configData.connections.brokers.length - 1 ? 'none' : '1px solid #333'
                      }}
                    >
                      <td style={{ padding: '12px 16px' }}>{broker.name}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${broker.environment === 'Live' ? 'danger' : 'warning'}`}>
                          {broker.environment}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${broker.status === 'Connected' ? 'success' : 'info'}`}>
                          {broker.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <h3>Data Providers</h3>
            <div style={{ 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px',
              overflow: 'hidden'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#333' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Provider</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Rate Limit</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Status</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left' }}>Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {configData.connections.dataProviders.map((provider, index) => (
                    <tr 
                      key={provider.name}
                      style={{ 
                        borderBottom: index === configData.connections.dataProviders.length - 1 ? 'none' : '1px solid #333'
                      }}
                    >
                      <td style={{ padding: '12px 16px' }}>{provider.name}</td>
                      <td style={{ padding: '12px 16px' }}>{provider.rateLimit}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${provider.status === 'Connected' ? 'success' : 'info'}`}>
                          {provider.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <h3>System Limits</h3>
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '16px'
              }}>
                {Object.entries(configData.systemLimits).map(([limitName, limitValue]) => (
                  <div key={limitName}>
                    <label style={{ display: 'block', marginBottom: '6px', color: '#9e9e9e' }}>
                      {limitName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </label>
                    <input
                      type="number"
                      value={limitValue}
                      onChange={(e) => handleInputChange('systemLimits', limitName, parseInt(e.target.value))}
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
            
            <h3>AI Settings</h3>
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '16px'
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
