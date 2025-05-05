const express = require('express');
const cors = require('cors');
const axios = require('axios');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 4000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Tradier proxy routes
app.all('/tradier/*', async (req, res) => {
  try {
    console.log('Tradier API request:', req.method, req.path);
    console.log('Headers:', JSON.stringify(req.headers));
    
    const tradierToken = req.headers['x-tradier-token'];
    if (!tradierToken) {
      console.error('Missing Tradier API token in request');
      return res.status(401).json({ error: 'Tradier API token is required' });
    }

    // Extract the actual API path
    const apiPath = req.path.replace('/tradier', '');
    const isPaper = req.headers['x-tradier-mode'] === 'paper';
    const baseUrl = isPaper ? 
      'https://sandbox.tradier.com/v1' : 
      'https://api.tradier.com/v1';
    
    console.log(`Forwarding to ${baseUrl}${apiPath}`);
    console.log('Token (first 5 chars):', tradierToken.substring(0, 5));
    
    // Forward the request to Tradier
    const response = await axios({
      method: req.method,
      url: `${baseUrl}${apiPath}`,
      data: req.method !== 'GET' ? req.body : undefined,
      params: req.method === 'GET' ? req.query : undefined,
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${tradierToken}`
      }
    });
    
    console.log('Tradier response status:', response.status);
    console.log('Tradier response data:', JSON.stringify(response.data).substring(0, 200) + '...');
    
    res.json(response.data);
  } catch (error) {
    console.error('Tradier proxy error:', error.message);
    if (error.response) {
      console.error('Tradier error status:', error.response.status);
      console.error('Tradier error response:', JSON.stringify(error.response.data));
      return res.status(error.response.status).json({ 
        error: error.message,
        data: error.response.data
      });
    }
    res.status(500).json({ error: error.message });
  }
});

// Alpaca proxy routes
app.all('/alpaca/*', async (req, res) => {
  try {
    console.log('Alpaca API request:', req.method, req.path);
    console.log('Headers:', JSON.stringify(req.headers));
    
    const alpacaKey = req.headers['x-alpaca-key'];
    const alpacaSecret = req.headers['x-alpaca-secret'];
    
    if (!alpacaKey || !alpacaSecret) {
      console.error('Missing Alpaca API credentials in request');
      return res.status(401).json({ error: 'Alpaca API credentials are required' });
    }

    // Extract the actual API path
    const apiPath = req.path.replace('/alpaca', '');
    const isPaper = req.headers['x-alpaca-mode'] === 'paper';
    const baseUrl = isPaper ? 
      'https://paper-api.alpaca.markets' : 
      'https://api.alpaca.markets';
    
    console.log(`Forwarding to ${baseUrl}${apiPath}`);
    console.log('Alpaca Key (first 5 chars):', alpacaKey.substring(0, 5));
    console.log('Alpaca Secret provided:', alpacaSecret ? 'Yes (hidden)' : 'No');
    
    // Forward the request to Alpaca
    const response = await axios({
      method: req.method,
      url: `${baseUrl}${apiPath}`,
      data: req.method !== 'GET' ? req.body : undefined,
      params: req.method === 'GET' ? req.query : undefined,
      headers: {
        'Accept': 'application/json',
        'APCA-API-KEY-ID': alpacaKey,
        'APCA-API-SECRET-KEY': alpacaSecret
      }
    });
    
    console.log('Alpaca response status:', response.status);
    console.log('Alpaca response data:', JSON.stringify(response.data).substring(0, 200) + '...');
    
    res.json(response.data);
  } catch (error) {
    console.error('Alpaca proxy error:', error.message);
    if (error.response) {
      console.error('Alpaca error status:', error.response.status);
      console.error('Alpaca error response:', JSON.stringify(error.response.data));
      return res.status(error.response.status).json({ 
        error: error.message,
        data: error.response.data
      });
    }
    res.status(500).json({ error: error.message });
  }
});

// Basic route to check if the server is running
app.get('/', (req, res) => {
  res.json({ status: 'API Proxy Server is running' });
});

// Test routes for direct API testing
app.get('/test/tradier', (req, res) => {
  console.log('Testing Tradier connection directly with hardcoded API keys');
  const tradierApiKey = 'KU2iUnOZIUFre0wypgyOn8TgmGxI';
  
  axios.get('https://api.tradier.com/v1/user/profile', {
    headers: {
      'Authorization': `Bearer ${tradierApiKey}`,
      'Accept': 'application/json'
    }
  })
  .then(response => {
    console.log('Direct Tradier test response:', response.status);
    res.json({
      success: true,
      data: response.data
    });
  })
  .catch(error => {
    console.error('Direct Tradier test error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  });
});

// Get Tradier account balances
app.get('/tradier/balances', (req, res) => {
  console.log('Getting Tradier account balances with hardcoded API keys');
  const tradierApiKey = 'KU2iUnOZIUFre0wypgyOn8TgmGxI';
  
  axios.get('https://api.tradier.com/v1/accounts/balances', {
    headers: {
      'Authorization': `Bearer ${tradierApiKey}`,
      'Accept': 'application/json'
    }
  })
  .then(response => {
    console.log('Tradier balances response:', response.status);
    res.json({
      success: true,
      data: response.data
    });
  })
  .catch(error => {
    console.error('Tradier balances error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  });
});

app.get('/test/alpaca', async (req, res) => {
  try {
    // Use the Alpaca API keys from our stored user memory
    const alpacaKey = 'PKYBHCCT1DIMGZX6P64A';
    const alpacaSecret = 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO';
    const baseUrl = 'https://paper-api.alpaca.markets';
    
    console.log('Testing Alpaca connection directly with hardcoded API keys');
    
    const response = await axios({
      method: 'GET',
      url: `${baseUrl}/v2/account`,
      headers: {
        'Accept': 'application/json',
        'APCA-API-KEY-ID': alpacaKey,
        'APCA-API-SECRET-KEY': alpacaSecret
      }
    });
    
    console.log('Direct Alpaca test response:', response.status);
    console.log('Response data:', JSON.stringify(response.data).substring(0, 200) + '...');
    
    res.json({
      success: true,
      status: response.status,
      data: response.data
    });
  } catch (error) {
    console.error('Direct Alpaca test error:', error.message);
    if (error.response) {
      return res.status(error.response.status).json({
        success: false,
        error: error.message,
        status: error.response.status,
        data: error.response.data
      });
    }
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get Alpaca account balance
app.get('/alpaca/account', (req, res) => {
  console.log('Getting Alpaca account information with hardcoded API keys');
  const alpacaKey = 'PKYBHCCT1DIMGZX6P64A';
  const alpacaSecret = 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO';
  const baseUrl = 'https://paper-api.alpaca.markets';
  
  axios.get(`${baseUrl}/v2/account`, {
    headers: {
      'APCA-API-KEY-ID': alpacaKey,
      'APCA-API-SECRET-KEY': alpacaSecret,
      'Accept': 'application/json'
    }
  })
  .then(response => {
    console.log('Alpaca account response:', response.status);
    res.json({
      success: true,
      data: response.data
    });
  })
  .catch(error => {
    console.error('Alpaca account error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  });
});

// Get Alpaca positions
app.get('/alpaca/positions', (req, res) => {
  console.log('Getting Alpaca positions with hardcoded API keys');
  const alpacaKey = 'PKYBHCCT1DIMGZX6P64A';
  const alpacaSecret = 'ssidJ2cJU0EGBOhdHrXJd7HegoaPaAMQqs0AU2PO';
  const baseUrl = 'https://paper-api.alpaca.markets';
  
  axios.get(`${baseUrl}/v2/positions`, {
    headers: {
      'APCA-API-KEY-ID': alpacaKey,
      'APCA-API-SECRET-KEY': alpacaSecret,
      'Accept': 'application/json'
    }
  })
  .then(response => {
    console.log('Alpaca positions response:', response.status);
    res.json({
      success: true,
      data: response.data
    });
  })
  .catch(error => {
    console.error('Alpaca positions error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`);
  console.log(`Tradier endpoint: http://localhost:${PORT}/tradier/`);
  console.log(`Alpaca endpoint: http://localhost:${PORT}/alpaca/`);
});
