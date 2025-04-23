import React from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';

const Dashboard = () => {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 240,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Portfolio Overview
            </Typography>
            <Typography variant="body2">
              Your trading portfolio information will be displayed here.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 240,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Trading Signals
            </Typography>
            <Typography variant="body2">
              Current trading signals will be displayed here.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 240,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Performance
            </Typography>
            <Typography variant="body2">
              Performance metrics will be displayed here.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 