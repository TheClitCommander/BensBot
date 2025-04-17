import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

// Components
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Performance from './pages/Performance';
import Settings from './pages/Settings';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

// Auth Components
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// Create theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

function App() {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Box sx={{ display: 'flex' }}>
                  <CssBaseline />
                  <Header handleDrawerToggle={handleDrawerToggle} />
                  <Sidebar mobileOpen={mobileOpen} handleDrawerToggle={handleDrawerToggle} />
                  <Box
                    component="main"
                    sx={{
                      flexGrow: 1,
                      p: 3,
                      width: { sm: `calc(100% - 240px)` },
                      mt: 8,
                    }}
                  >
                    <Dashboard />
                  </Box>
                </Box>
              </ProtectedRoute>
            } />
            
            <Route path="/strategies" element={
              <ProtectedRoute>
                <Box sx={{ display: 'flex' }}>
                  <CssBaseline />
                  <Header handleDrawerToggle={handleDrawerToggle} />
                  <Sidebar mobileOpen={mobileOpen} handleDrawerToggle={handleDrawerToggle} />
                  <Box
                    component="main"
                    sx={{
                      flexGrow: 1,
                      p: 3,
                      width: { sm: `calc(100% - 240px)` },
                      mt: 8,
                    }}
                  >
                    <Strategies />
                  </Box>
                </Box>
              </ProtectedRoute>
            } />
            
            <Route path="/performance" element={
              <ProtectedRoute>
                <Box sx={{ display: 'flex' }}>
                  <CssBaseline />
                  <Header handleDrawerToggle={handleDrawerToggle} />
                  <Sidebar mobileOpen={mobileOpen} handleDrawerToggle={handleDrawerToggle} />
                  <Box
                    component="main"
                    sx={{
                      flexGrow: 1,
                      p: 3,
                      width: { sm: `calc(100% - 240px)` },
                      mt: 8,
                    }}
                  >
                    <Performance />
                  </Box>
                </Box>
              </ProtectedRoute>
            } />
            
            <Route path="/settings" element={
              <ProtectedRoute>
                <Box sx={{ display: 'flex' }}>
                  <CssBaseline />
                  <Header handleDrawerToggle={handleDrawerToggle} />
                  <Sidebar mobileOpen={mobileOpen} handleDrawerToggle={handleDrawerToggle} />
                  <Box
                    component="main"
                    sx={{
                      flexGrow: 1,
                      p: 3,
                      width: { sm: `calc(100% - 240px)` },
                      mt: 8,
                    }}
                  >
                    <Settings />
                  </Box>
                </Box>
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App; 