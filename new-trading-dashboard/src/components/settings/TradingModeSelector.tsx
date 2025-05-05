import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './settings.css'; // We'll create this CSS file later

const TradingModeSelector: React.FC = () => {
  const [isPaperTrading, setIsPaperTrading] = useState<boolean>(true);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState<boolean>(false);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'info', visible: boolean}>({ 
    message: '', 
    type: 'info', 
    visible: false 
  });
  
  useEffect(() => {
    // Get current trading mode on component mount
    try {
      const currentMode = api.trading.getTradingMode();
      setIsPaperTrading(currentMode.isPaperTrading);
    } catch (error) {
      console.error('Error getting trading mode:', error);
      // Default to paper trading if there's an error
      setIsPaperTrading(true);
    }
  }, []);

  // Show notification for 5 seconds then hide it
  useEffect(() => {
    if (notification.visible) {
      const timer = setTimeout(() => {
        setNotification(prev => ({ ...prev, visible: false }));
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification.visible]);

  const handleSwitchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.checked;
    
    // If switching to live trading (unchecked means live), show confirmation dialog
    if (!newValue) {
      setConfirmDialogOpen(true);
    } else {
      // Switching to paper trading is always allowed without confirmation
      applyTradingModeChange(true);
    }
  };

  const applyTradingModeChange = (usePaperTrading: boolean) => {
    try {
      // Call the API function to change trading mode
      api.trading.switchTradingMode(usePaperTrading);
      setIsPaperTrading(usePaperTrading);
      
      // Show success notification
      setNotification({
        message: `Switched to ${usePaperTrading ? 'paper' : 'live'} trading mode`,
        type: 'success',
        visible: true
      });
    } catch (error) {
      console.error('Error switching trading mode:', error);
      
      // Show error notification
      setNotification({
        message: `Failed to switch trading mode: ${error instanceof Error ? error.message : String(error)}`,
        type: 'error',
        visible: true
      });
    }
  };

  const handleConfirmLiveTrading = () => {
    setConfirmDialogOpen(false);
    applyTradingModeChange(false);
  };

  const handleCancelLiveTrading = () => {
    setConfirmDialogOpen(false);
    // Reset the switch to paper trading
    setIsPaperTrading(true);
  };

  return (
    <div className="settings-card">
      <div className="settings-card-content">
        <div className="settings-header">
          <h3>Trading Mode</h3>
          <span className={`mode-badge ${isPaperTrading ? 'paper' : 'live'}`}>
            {isPaperTrading ? "Paper Trading" : "Live Trading"}
          </span>
        </div>
        
        <div className="settings-row">
          <label className="switch-label">
            <span>
              {isPaperTrading ? "Paper Trading (simulated)" : "Live Trading (real money)"}
              {!isPaperTrading && <span className="warning-icon">⚠️</span>}
            </span>
            <div className="toggle-switch">
              <input
                type="checkbox"
                checked={isPaperTrading}
                onChange={handleSwitchChange}
              />
              <span className="slider"></span>
            </div>
          </label>
          
          <p className="hint-text">
            {isPaperTrading
              ? "Paper trading uses simulated accounts with fake money for testing. No real trades will be executed."
              : "CAUTION: Live trading uses real money and executes actual trades. Make sure you understand the risks."
            }
          </p>
        </div>
      </div>
      
      {/* Confirmation Dialog for Live Trading */}
      {confirmDialogOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header danger">
              <span className="warning-icon">⚠️</span>
              <h3>Enable Live Trading?</h3>
            </div>
            <div className="modal-body">
              <p>
                You are about to switch to LIVE TRADING mode. This will use REAL MONEY and execute ACTUAL TRADES using your brokerage account.
              </p>
              <ul>
                <li>All trades will be executed with real funds</li>
                <li>Your actual portfolio will be affected</li>
                <li>Market orders will be sent to your broker</li>
              </ul>
              <p><strong>Are you absolutely sure you want to continue?</strong></p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-neutral" onClick={handleCancelLiveTrading}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleConfirmLiveTrading}>
                Yes, Enable Live Trading
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Notification */}
      {notification.visible && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
          <button className="close-btn" onClick={() => setNotification(prev => ({ ...prev, visible: false }))}>
            ×
          </button>
        </div>
      )}
    </div>
  );
};

export default TradingModeSelector;
