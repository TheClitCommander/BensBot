import React from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';

const Strategies = () => {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Strategies
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
              Available Strategies
            </Typography>
            <Typography variant="body2">
              Your trading strategies will be displayed here.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Strategies; 