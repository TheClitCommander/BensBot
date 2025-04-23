import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Create auth context
const AuthContext = createContext();

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper function to get token from localStorage
const getStoredToken = () => {
  const token = localStorage.getItem('token');
  const refreshToken = localStorage.getItem('refreshToken');
  return { token, refreshToken };
};

// Create provider component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const storedTokens = getStoredToken();
      
      if (storedTokens.token) {
        setToken(storedTokens.token);
        setRefreshToken(storedTokens.refreshToken);
        
        try {
          // Verify token by getting user info
          const user = await fetchCurrentUser(storedTokens.token);
          setCurrentUser(user);
        } catch (error) {
          // Token is invalid, try refresh
          try {
            if (storedTokens.refreshToken) {
              await refreshTokens(storedTokens.refreshToken);
            }
          } catch (refreshError) {
            // Refresh failed, clear everything
            logout();
          }
        }
      }
      
      setLoading(false);
    };
    
    initAuth();
  }, []);

  // Create authenticated axios instance
  const authAxios = axios.create({
    baseURL: API_URL
  });
  
  // Add auth token to requests
  authAxios.interceptors.request.use(
    (config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
  
  // Handle token refresh on 401 errors
  authAxios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      // If error is 401 and we haven't tried to refresh yet
      if (error.response?.status === 401 && !originalRequest._retry && refreshToken) {
        originalRequest._retry = true;
        
        try {
          // Try to refresh the token
          await refreshTokens(refreshToken);
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout
          logout();
          return Promise.reject(refreshError);
        }
      }
      
      return Promise.reject(error);
    }
  );

  // Fetch current user info
  const fetchCurrentUser = async (userToken) => {
    const config = {
      headers: { Authorization: `Bearer ${userToken || token}` }
    };
    
    const response = await axios.get(`${API_URL}/api/auth/me`, config);
    return response.data;
  };

  // Refresh tokens
  const refreshTokens = async (userRefreshToken) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/refresh`, {
        refresh_token: userRefreshToken || refreshToken
      });
      
      const { access_token, refresh_token } = response.data;
      
      // Update tokens
      setToken(access_token);
      setRefreshToken(refresh_token);
      
      // Store tokens
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // Get user info with new token
      const user = await fetchCurrentUser(access_token);
      setCurrentUser(user);
      
      return { access_token, refresh_token };
    } catch (error) {
      throw new Error('Failed to refresh token');
    }
  };

  // Register a new user
  const register = async (username, email, password) => {
    try {
      await axios.post(`${API_URL}/api/auth/register`, {
        username,
        email,
        password
      });
      
      // Registration successful, user should log in
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      throw new Error(message);
    }
  };

  // Login user
  const login = async (username, password) => {
    try {
      // Format data as form data for OAuth2 compatibility
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post(`${API_URL}/api/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token, refresh_token } = response.data;
      
      // Store tokens
      setToken(access_token);
      setRefreshToken(refresh_token);
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // Get user info
      const user = await fetchCurrentUser(access_token);
      setCurrentUser(user);
      
      return user;
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      throw new Error(message);
    }
  };

  // Logout user
  const logout = () => {
    // Clear user and tokens
    setCurrentUser(null);
    setToken(null);
    setRefreshToken(null);
    
    // Remove from storage
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  };

  // Context value
  const value = {
    currentUser,
    loading,
    token,
    register,
    login,
    logout,
    refreshTokens,
    authAxios
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

export default AuthContext; 