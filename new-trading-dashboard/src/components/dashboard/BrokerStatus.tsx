import React, { useState, useEffect, FC } from 'react';
import * as api from '../../services/api';
import axios from 'axios';
import '../settings/settings.css';

interface StatusItem {
  name: string;
  isConnected: boolean;
  statusMessage: string;
  isCurrent: boolean;
}

// Helper function to check if the broker has API keys configured
function brokerHasKeys(broker: string): boolean {
  if (broker === 'tradier') {
    return !!localStorage.getItem('tradier_api_key');
  } else if (broker === 'alpaca') {
    return !!localStorage.getItem('alpaca_api_key') && !!localStorage.getItem('alpaca_api_secret');
  } else if (broker === 'etrade') {
    return !!localStorage.getItem('etrade_key') && !!localStorage.getItem('etrade_secret');
  }
  return false;
}

const BrokerStatus: FC = () => {
  const [brokerStatus, setBrokerStatus] = useState<StatusItem[]>([]);
  const [infoOpen, setInfoOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Add a small delay to ensure API connections have been attempted
    const timer = setTimeout(() => {
      checkBrokerConnections();
    }, 1000); // 1 second delay
    
    return () => clearTimeout(timer);
  }, []);

  const checkBrokerConnections = async () => {
    setIsLoading(true);
    
    try {
      // Get the current trading mode from localStorage
      const isPaperTrading = localStorage.getItem('paper_trading') !== 'false';
      
      // Get the selected portfolio
      const selectedPortfolio = localStorage.getItem('selectedPortfolio') || 'alpaca';
      
      // Check individual broker connections
      const tradierStatus = await testBrokerConnection('tradier');
      const alpacaStatus = await testBrokerConnection('alpaca');
      const etradeStatus = !isPaperTrading ? 
        await testBrokerConnection('etrade') : 
        { isConnected: false, message: 'E*TRADE not available in paper mode' };
      
      // Create status array
      const statusArray: StatusItem[] = [
        {
          name: 'Tradier',
          isConnected: tradierStatus.isConnected,
          statusMessage: tradierStatus.message,
          isCurrent: selectedPortfolio.includes('tradier')
        },
        {
          name: 'Alpaca',
          isConnected: alpacaStatus.isConnected,
          statusMessage: alpacaStatus.message,
          isCurrent: selectedPortfolio.includes('alpaca')
        }
      ];
      
      // Add E*TRADE if in live mode
      if (!isPaperTrading) {
        statusArray.push({
          name: 'E*TRADE',
          isConnected: etradeStatus.isConnected,
          statusMessage: etradeStatus.message,
          isCurrent: selectedPortfolio.includes('etrade')
        });
      }
      
      setBrokerStatus(statusArray);
    } catch (error) {
      console.error('Error checking broker connections:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const testBrokerConnection = async (broker: string): Promise<{isConnected: boolean, message: string}> => {
    try {
      console.log(`Testing ${broker} connection...`);
      
      // Check if we have keys for this broker
      const hasKeys = brokerHasKeys(broker);
      if (!hasKeys) {
        console.log(`No API keys configured for ${broker}`);
        return { isConnected: false, message: `No API keys configured for ${broker}` };
      }
      
      // Check if we have stored connection status (faster response)
      const storedStatus = localStorage.getItem(`${broker}_connected`);
      if (storedStatus === 'true') {
        console.log(`Using stored connection status for ${broker}`);
        return { isConnected: true, message: `Connected to ${broker}` };
      }
      
      // For immediate feedback, we'll default to false and let the background 
      // API calls update the status later
      console.log(`No stored connection status for ${broker}`);
      return { isConnected: false, message: `Connection status for ${broker} pending...` };
      
    } catch (error) {
      console.error(`Error testing ${broker} connection:`, error);
      return { isConnected: false, message: `Error connecting to ${broker}` };
    }
  };

  return (
    <div className="broker-status">
      <span className="broker-status-label">Broker Status:</span>
      
      {isLoading ? (
        <span className="broker-chip">Loading...</span>
      ) : (
        <>
          {brokerStatus.map((status) => (
            <div 
              key={status.name}
              className={`broker-chip ${status.isConnected ? 'connected' : 'disconnected'} ${status.isCurrent ? 'active' : ''}`}
              title={`${status.name}: ${status.statusMessage}`}
            >
              <span className="status-icon">
                {status.isConnected ? '✅' : '❌'}
              </span>
              {status.name}
            </div>
          ))}
        </>
      )}
      
      <button 
        className="broker-info-btn" 
        onClick={() => setInfoOpen(true)}
        title="View connection details"
      >
        ℹ️
      </button>
      
      {infoOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Broker Connection Details</h3>
              <button className="close-btn" onClick={() => setInfoOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <p>
                {localStorage.getItem('paper_trading') !== 'false'
                  ? 'Currently in PAPER trading mode. Using sandbox/paper trading accounts.' 
                  : 'Currently in LIVE trading mode. Using real brokerage accounts.'}
              </p>
              
              {brokerStatus.map((status) => (
                <div className="settings-card" key={status.name}>
                  <div className="settings-card-content">
                    <div className="settings-header">
                      <h4>{status.name}</h4>
                      <div className="status-badges">
                        <span className={`mode-badge ${status.isConnected ? 'paper' : 'live'}`}>
                          {status.isConnected ? 'Connected' : 'Not Connected'}
                        </span>
                        {status.isCurrent && (
                          <span className="mode-badge active">Active</span>
                        )}
                      </div>
                    </div>
                    <p className="hint-text">
                      Status: {status.statusMessage}
                    </p>
                  </div>
                </div>
              ))}
              
              <p className="hint-text">
                You can update your API keys and broker preferences in the Settings page.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BrokerStatus;
