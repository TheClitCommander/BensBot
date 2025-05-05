import React from 'react';
import { Box, Paper, Typography } from '@mui/material';

const SignalGauge = ({ value, title }) => {
  // Normalize value to ensure it's between -1 and 1
  const normalizedValue = Math.max(-1, Math.min(1, value));
  
  // Calculate angle for the gauge needle (from -45 to 225 degrees)
  const angle = 135 + (normalizedValue * 135);
  
  // Calculate color based on signal value
  const getColor = (val) => {
    if (val > 0.7) return '#4caf50'; // Strong buy - green
    if (val > 0.3) return '#8bc34a'; // Buy - light green
    if (val > -0.3) return '#ffc107'; // Neutral - yellow
    if (val > -0.7) return '#ff9800'; // Sell - orange
    return '#f44336'; // Strong sell - red
  };
  
  const color = getColor(normalizedValue);
  
  // Format signal value as a percentage with sign
  const formatSignal = (val) => {
    const percentage = Math.abs(val * 100).toFixed(1);
    if (val > 0) return `+${percentage}%`;
    if (val < 0) return `-${percentage}%`;
    return '0%';
  };
  
  // Get signal description
  const getSignalDescription = (val) => {
    if (val > 0.7) return 'Strong Buy';
    if (val > 0.3) return 'Buy';
    if (val > -0.3) return 'Neutral';
    if (val > -0.7) return 'Sell';
    return 'Strong Sell';
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Typography variant="h6" color="primary" gutterBottom>
        {title || 'Trading Signal'}
      </Typography>
      
      {/* Gauge */}
      <Box
        sx={{
          position: 'relative',
          width: 200,
          height: 100,
          mt: 2,
          mb: 4,
        }}
      >
        {/* Gauge background */}
        <Box
          sx={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            borderRadius: '100px 100px 0 0',
            background: 'linear-gradient(90deg, #f44336 0%, #ffc107 50%, #4caf50 100%)',
            opacity: 0.3,
          }}
        />
        
        {/* Gauge needle */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: '50%',
            width: 4,
            height: 90,
            backgroundColor: 'grey.800',
            transformOrigin: 'bottom center',
            transform: `translateX(-50%) rotate(${angle}deg)`,
            transition: 'transform 0.5s ease-out',
            '&::after': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: -4,
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: 'grey.800',
            }
          }}
        />
        
        {/* Gauge markers */}
        <Box sx={{ 
          position: 'absolute', 
          bottom: -10, 
          left: 0, 
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <Typography variant="caption" sx={{ transform: 'rotate(-45deg)', color: '#f44336' }}>
            -100%
          </Typography>
          <Typography variant="caption" sx={{ color: '#ffc107' }}>
            0%
          </Typography>
          <Typography variant="caption" sx={{ transform: 'rotate(45deg)', color: '#4caf50' }}>
            +100%
          </Typography>
        </Box>
      </Box>
      
      {/* Signal value */}
      <Typography 
        variant="h4" 
        align="center"
        sx={{ 
          fontWeight: 'bold',
          color: color,
          mb: 1
        }}
      >
        {formatSignal(normalizedValue)}
      </Typography>
      
      {/* Signal description */}
      <Typography variant="subtitle1" align="center" color="text.secondary">
        {getSignalDescription(normalizedValue)}
      </Typography>
    </Paper>
  );
};

export default SignalGauge; 