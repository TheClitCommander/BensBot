import React, { useState, useEffect } from 'react';
import api, { testServerClient } from '../../services/api';
import '../settings/settings.css';

interface Portfolio {
  id: string;
  name: string;
  broker: string;
  accountNumber: string;
  isPaper: boolean;
}

interface PortfolioSelectorProps {
  onChange?: (portfolioId: string) => void;
}

const PortfolioSelector: React.FC<PortfolioSelectorProps> = ({ onChange }) => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Load available portfolios when component mounts
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    setIsLoading(true);
    try {
      // Initialize available portfolios array
      const availablePortfolios: Portfolio[] = [];
      
      // Get trading mode - just for reference
      const tradingMode = api.trading.getTradingMode();
      
      // Try to get Tradier portfolio directly
      try {
        const tradierResponse = await testServerClient.get('/test/tradier');
        if (tradierResponse.data && tradierResponse.data.success) {
          // Get account data from response
          const tradierProfileData = tradierResponse.data.data?.profile;
          const tradierAccountNumber = tradierProfileData?.account?.account_number || 'VA1201776';
          
          // Add Tradier portfolio
          availablePortfolios.push({
            id: 'tradier_paper',
            name: 'Tradier Paper Trading',
            broker: 'tradier',
            accountNumber: tradierAccountNumber,
            isPaper: true
          });
          
          console.log('Added Tradier portfolio with account number:', tradierAccountNumber);
        }
      } catch (error) {
        console.error('Error getting Tradier account info:', error);
      }
      
      // Try to get Alpaca portfolio directly
      try {
        const alpacaResponse = await testServerClient.get('/test/alpaca');
        if (alpacaResponse.data && alpacaResponse.data.success) {
          // Get account data from response
          const alpacaAccountData = alpacaResponse.data.data;
          const alpacaAccountNumber = alpacaAccountData?.account_number || 'PA3PBZ3WQVSL';
          
          // Add Alpaca portfolio
          availablePortfolios.push({
            id: 'alpaca_paper',
            name: 'Alpaca Paper Trading',
            broker: 'alpaca',
            accountNumber: alpacaAccountNumber,
            isPaper: true
          });
          
          console.log('Added Alpaca portfolio with account number:', alpacaAccountNumber);
        }
      } catch (error) {
        console.error('Error getting Alpaca account info:', error);
      }
      
      // Add E*TRADE portfolio if it's configured
      if (tradingMode.brokers.etrade.isConfigured) {
        availablePortfolios.push({
          id: 'etrade_live',
          name: 'E*TRADE Live Trading',
          broker: 'etrade',
          accountNumber: 'Not Available',
          isPaper: false
        });
      }
      
      // If no portfolios are available, add a mock portfolio
      if (availablePortfolios.length === 0) {
        availablePortfolios.push({
          id: 'mock',
          name: 'Mock Portfolio (Demo)',
          broker: 'mock',
          accountNumber: 'DEMO-123',
          isPaper: true
        });
      }
      
      setPortfolios(availablePortfolios);
      
      // Select the first portfolio by default if none is selected
      if (!selectedPortfolio && availablePortfolios.length > 0) {
        setSelectedPortfolio(availablePortfolios[0].id);
        if (onChange) {
          onChange(availablePortfolios[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading portfolios:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePortfolioChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newPortfolioId = event.target.value;
    setSelectedPortfolio(newPortfolioId);
    
    // Notify parent component of the change
    if (onChange) {
      onChange(newPortfolioId);
    }
    
    // Store the selected portfolio in localStorage
    localStorage.setItem('selected_portfolio_id', newPortfolioId);
  };

  return (
    <div className="portfolio-selector">
      <label htmlFor="portfolio-select">Portfolio: </label>
      <select 
        id="portfolio-select"
        value={selectedPortfolio}
        onChange={handlePortfolioChange}
        disabled={isLoading}
      >
        {isLoading ? (
          <option value="">Loading portfolios...</option>
        ) : (
          portfolios.map(portfolio => (
            <option key={portfolio.id} value={portfolio.id}>
              {portfolio.name} ({portfolio.accountNumber})
            </option>
          ))
        )}
      </select>
    </div>
  );
};

export default PortfolioSelector;
