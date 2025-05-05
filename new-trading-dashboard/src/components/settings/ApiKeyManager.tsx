import React, { useState, useEffect } from 'react';
// Import MUI components using require instead of import
const Card: React.ComponentType<any> = require('@mui/material').Card;
const CardContent: React.ComponentType<any> = require('@mui/material').CardContent;
const Typography: React.ComponentType<any> = require('@mui/material').Typography;
const Box: React.ComponentType<any> = require('@mui/material').Box;
const TextField: React.ComponentType<any> = require('@mui/material').TextField;
const Button: React.ComponentType<any> = require('@mui/material').Button;
const Grid: React.ComponentType<any> = require('@mui/material').Grid;
const Accordion: React.ComponentType<any> = require('@mui/material').Accordion;
const AccordionSummary: React.ComponentType<any> = require('@mui/material').AccordionSummary;
const AccordionDetails: React.ComponentType<any> = require('@mui/material').AccordionDetails;
const Divider: React.ComponentType<any> = require('@mui/material').Divider;
const Chip: React.ComponentType<any> = require('@mui/material').Chip;
const InputAdornment: React.ComponentType<any> = require('@mui/material').InputAdornment;
const IconButton: React.ComponentType<any> = require('@mui/material').IconButton;
const Alert: React.ComponentType<any> = require('@mui/material').Alert;
const Paper: React.ComponentType<any> = require('@mui/material').Paper;
// Import MUI icons
const ExpandMoreIcon: React.ComponentType<any> = require('@mui/icons-material/ExpandMore').default;
const Visibility: React.ComponentType<any> = require('@mui/icons-material/Visibility').default;
const VisibilityOff: React.ComponentType<any> = require('@mui/icons-material/VisibilityOff').default;
const CheckCircleIcon: React.ComponentType<any> = require('@mui/icons-material/CheckCircle').default;
const ErrorIcon: React.ComponentType<any> = require('@mui/icons-material/Error').default;
import api from '../../services/api';

interface ApiKeySet {
  [key: string]: string;
}

interface ApiKeyConfig {
  id: string;
  label: string;
  description: string;
  placeholder: string;
  isSecret?: boolean;
  isSaved?: boolean;
}

const ApiKeyManager: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeySet>({});
  const [showSecrets, setShowSecrets] = useState<{[key: string]: boolean}>({});
  const [savedStatus, setSavedStatus] = useState<{[key: string]: boolean}>({});
  const [expandedAccordion, setExpandedAccordion] = useState<string>('tradier');
  const [etradeAuthUrl, setEtradeAuthUrl] = useState<string>('');
  const [etradeVerifier, setEtradeVerifier] = useState<string>('');
  const [etradeRequestToken, setEtradeRequestToken] = useState<string>('');
  const [isAuthenticating, setIsAuthenticating] = useState<boolean>(false);

  // Trading mode from context
  const isPaperTrading = api.trading.getTradingMode().isPaperTrading;
  
  // Configuration for API key fields
  const brokerConfigs = {
    tradier: [
      {
        id: isPaperTrading ? 'tradier_token_paper' : 'tradier_token_live',
        label: isPaperTrading ? 'Tradier Paper API Token' : 'Tradier Live API Token',
        description: `${isPaperTrading ? 'Sandbox' : 'Production'} API token from Tradier developer dashboard`,
        placeholder: 'Bearer xxxxxxxxxxxxxxxxxxxxxxxx',
        isSecret: true
      }
    ],
    alpaca: [
      {
        id: isPaperTrading ? 'paper_alpaca_key' : 'alpaca_key',
        label: isPaperTrading ? 'Alpaca Paper API Key' : 'Alpaca Live API Key',
        description: `${isPaperTrading ? 'Paper' : 'Live'} trading API key from Alpaca dashboard`,
        placeholder: 'AKXXXXXXXXXXXXXXXX'
      },
      {
        id: isPaperTrading ? 'paper_alpaca_secret' : 'alpaca_secret',
        label: isPaperTrading ? 'Alpaca Paper API Secret' : 'Alpaca Live API Secret',
        description: `${isPaperTrading ? 'Paper' : 'Live'} trading API secret from Alpaca dashboard`,
        placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        isSecret: true
      }
    ],
    etrade: !isPaperTrading ? [
      {
        id: 'etrade_key',
        label: 'E*TRADE Consumer Key',
        description: 'Consumer key from E*TRADE developer dashboard',
        placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxx'
      },
      {
        id: 'etrade_secret',
        label: 'E*TRADE Consumer Secret',
        description: 'Consumer secret from E*TRADE developer dashboard',
        placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxx',
        isSecret: true
      }
    ] : []
  };

  const marketDataConfigs = [
    {
      id: 'alpha_vantage_key',
      label: 'Alpha Vantage API Key',
      description: 'For market data and company fundamentals',
      placeholder: 'xxxxxxxxxxxxxxxx'
    },
    {
      id: 'finnhub_key',
      label: 'Finnhub API Key',
      description: 'For real-time price data and news',
      placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxx'
    }
  ];

  useEffect(() => {
    loadSavedApiKeys();
  }, [isPaperTrading]); // Reload when trading mode changes

  const loadSavedApiKeys = () => {
    const keys: ApiKeySet = {};
    const status: {[key: string]: boolean} = {};
    
    // Load broker keys
    Object.values(brokerConfigs).flat().forEach(config => {
      const value = localStorage.getItem(config.id) || '';
      keys[config.id] = value;
      status[config.id] = !!value;
    });
    
    // Load market data keys
    marketDataConfigs.forEach(config => {
      const value = localStorage.getItem(config.id) || '';
      keys[config.id] = value;
      status[config.id] = !!value;
    });
    
    setApiKeys(keys);
    setSavedStatus(status);
  };

  const handleKeyChange = (id: string, value: string) => {
    setApiKeys(prev => ({ ...prev, [id]: value }));
  };

  const saveApiKey = (id: string) => {
    try {
      localStorage.setItem(id, apiKeys[id] || '');
      setSavedStatus(prev => ({ ...prev, [id]: true }));
      
      // If this is a broker key, we need to reload the API client configs
      if (id.includes('tradier') || id.includes('alpaca') || id.includes('etrade')) {
        api.trading.switchTradingMode(isPaperTrading); // This reloads the API keys
      }
    } catch (error) {
      console.error(`Error saving API key ${id}:`, error);
      alert(`Failed to save API key: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const toggleShowSecret = (id: string) => {
    setShowSecrets(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const startEtradeAuth = async () => {
    try {
      setIsAuthenticating(true);
      const result = await api.etradeOAuth.initiateOAuth();
      setEtradeAuthUrl(result.authUrl);
      setEtradeRequestToken(result.requestToken);
    } catch (error) {
      console.error('Error starting E*TRADE authentication:', error);
      alert(`Failed to start E*TRADE authentication: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsAuthenticating(false);
    }
  };

  const completeEtradeAuth = async () => {
    try {
      setIsAuthenticating(true);
      await api.etradeOAuth.completeOAuth(etradeRequestToken, etradeVerifier);
      setEtradeAuthUrl('');
      setEtradeVerifier('');
      setEtradeRequestToken('');
      alert('E*TRADE authentication successful!');
    } catch (error) {
      console.error('Error completing E*TRADE authentication:', error);
      alert(`Failed to complete E*TRADE authentication: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? panel : '');
  };

  const renderApiKeyInputs = (configs: ApiKeyConfig[]) => {
    return configs.map(config => (
      <Box key={config.id} sx={{ mb: 3, width: '100%' }}>
        <Box display="flex" alignItems="center" mb={1}>
          <Typography variant="subtitle1">{config.label}</Typography>
          {savedStatus[config.id] && (
            <Chip 
              icon={<CheckCircleIcon />} 
              label="Saved" 
              color="success" 
              size="small" 
              sx={{ ml: 2 }} 
            />
          )}
        </Box>
        <Typography variant="body2" color="textSecondary" mb={1}>{config.description}</Typography>
        <Box display="flex" alignItems="center">
          <TextField
            fullWidth
            variant="outlined"
            placeholder={config.placeholder}
            value={apiKeys[config.id] || ''}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleKeyChange(config.id, e.target.value)}
            type={config.isSecret && !showSecrets[config.id] ? 'password' : 'text'}
            InputProps={{
              endAdornment: config.isSecret ? (
                <InputAdornment position="end">
                  <IconButton onClick={() => toggleShowSecret(config.id)} edge="end">
                    {showSecrets[config.id] ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ) : undefined
            }}
          />
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => saveApiKey(config.id)}
            sx={{ ml: 2, whiteSpace: 'nowrap' }}
          >
            Save Key
          </Button>
        </Box>
      </Box>
    ));
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          API Key Management
        </Typography>
        
        <Box sx={{ mb: 4 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            You are currently in <strong>{isPaperTrading ? 'PAPER' : 'LIVE'}</strong> trading mode. 
            {isPaperTrading ? ' API keys will be used for paper/sandbox environments.' : ' API keys will be used for REAL trading.'}
          </Alert>
        </Box>

        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>Brokerage API Keys</Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Configure your brokerage API keys to enable real trading and portfolio data. 
            These are specific to {isPaperTrading ? 'paper/sandbox' : 'live'} trading mode.
          </Typography>
          
          {/* Tradier */}
          <Accordion 
            expanded={expandedAccordion === 'tradier'} 
            onChange={handleAccordionChange('tradier')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Tradier API Keys</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {renderApiKeyInputs(brokerConfigs.tradier)}
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* Alpaca */}
          <Accordion 
            expanded={expandedAccordion === 'alpaca'} 
            onChange={handleAccordionChange('alpaca')}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Alpaca API Keys</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {renderApiKeyInputs(brokerConfigs.alpaca)}
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* E*TRADE - Only shown in live trading mode */}
          {!isPaperTrading && (
            <Accordion 
              expanded={expandedAccordion === 'etrade'} 
              onChange={handleAccordionChange('etrade')}
              sx={{ mb: 2 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">E*TRADE API Keys & OAuth</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ width: '100%' }}>
                  {renderApiKeyInputs(brokerConfigs.etrade)}
                  
                  <Box sx={{ width: '100%' }}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" sx={{ mb: 2 }}>E*TRADE OAuth Authentication</Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      E*TRADE requires OAuth authentication for API access. First save your API keys above, then complete the OAuth flow.
                    </Typography>
                    
                    {!etradeAuthUrl ? (
                      <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={startEtradeAuth}
                        disabled={isAuthenticating}
                      >
                        Start E*TRADE Authentication
                      </Button>
                    ) : (
                      <Box>
                        <Alert severity="info" sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            1. <a href={etradeAuthUrl} target="_blank" rel="noopener noreferrer">Click here to authorize</a> with E*TRADE<br />
                            2. Log in to your E*TRADE account and allow access<br />
                            3. Enter the verification code provided by E*TRADE below
                          </Typography>
                        </Alert>
                        
                        <Box display="flex" alignItems="center">
                          <TextField
                            label="Verification Code"
                            value={etradeVerifier}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEtradeVerifier(e.target.value)}
                            sx={{ mr: 2 }}
                          />
                          <Button 
                            variant="contained" 
                            color="primary" 
                            onClick={completeEtradeAuth}
                            disabled={!etradeVerifier || isAuthenticating}
                          >
                            Complete Authentication
                          </Button>
                        </Box>
                      </Box>
                    )}
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </Box>
        
        <Box>
          <Typography variant="h6" gutterBottom>Market Data API Keys</Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Configure additional market data API keys to enhance data quality and reduce dependency on broker APIs.
            These keys are used in both paper and live trading modes.
          </Typography>
          
          <Accordion expanded={expandedAccordion === 'market'} onChange={handleAccordionChange('market')}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Market Data API Keys</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ width: '100%' }}>
                {renderApiKeyInputs(marketDataConfigs)}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ApiKeyManager;
