import React from 'react';
import { Box, Typography, Grid, Paper, Button } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Settings = () => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 240,
            }}
          >
            <Typography variant="h6" gutterBottom>
              User Profile
            </Typography>
            {currentUser && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body1">
                  <strong>Username:</strong> {currentUser.username}
                </Typography>
                <Typography variant="body1">
                  <strong>Email:</strong> {currentUser.email}
                </Typography>
                <Typography variant="body1">
                  <strong>Role:</strong> {currentUser.is_admin ? 'Administrator' : 'User'}
                </Typography>
              </Box>
            )}
            <Button 
              variant="contained" 
              color="error" 
              onClick={handleLogout}
              sx={{ mt: 2, alignSelf: 'flex-start' }}
            >
              Logout
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings; 