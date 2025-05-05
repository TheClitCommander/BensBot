import React from 'react';
import { Container, Typography, Box, Paper, Divider } from '@mui/material';
import TradingModeSelector from '../components/settings/TradingModeSelector';
import ApiKeyManager from '../components/settings/ApiKeyManager';

const Settings: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h4" gutterBottom>Settings</Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Configure your trading dashboard settings and API connections
        </Typography>
      </Paper>
      
      <Box sx={{ mb: 4 }}>
        <TradingModeSelector />
      </Box>
      
      <Box>
        <ApiKeyManager />
      </Box>
    </Container>
  );
};

export default Settings;
