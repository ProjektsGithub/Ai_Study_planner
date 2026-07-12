import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import apiClient from '../api/client';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [roles, setRoles] = useState([]);

  // Decode JWT access token to get roles
  const decodeToken = (token) => {
    if (!token) return null;
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        window.atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('Failed to decode token:', e);
      return null;
    }
  };

  useEffect(() => {
    // Check if user is logged in on mount
    if (token) {
      const decoded = decodeToken(token);
      if (decoded && decoded.roles) {
        setRoles(decoded.roles);
      } else {
        setRoles([]);
      }
      // Verify token and get user info
      fetchUserProfile();
    } else {
      setRoles([]);
      setLoading(false);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await apiClient.get('/api/v1/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Only logout if it's an authentication error (401), not other errors
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        email,
        password
      });

      const { access_token, refresh_token } = response.data;
      
      // Save tokens to localStorage first
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Update token state
      setToken(access_token);
      
      // Fetch user profile with the new token
      try {
        const profileResponse = await apiClient.get('/api/v1/auth/me', {
          headers: {
            Authorization: `Bearer ${access_token}`
          }
        });
        setUser(profileResponse.data);
        setLoading(false);
      } catch (profileError) {
        console.error('Failed to fetch user profile after login:', profileError);
        // Don't fail the login if profile fetch fails
      }
      
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  const register = async (email, password, fullName) => {
    try {
      await apiClient.post('/api/v1/auth/register', {
        email,
        password,
        name: fullName  // Backend expects 'name' not 'full_name'
      });

      // Auto-login after registration
      return await login(email, password);
    } catch (error) {
      // Handle validation errors from backend
      let errorMessage = 'Registration failed';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // If detail is an array of validation errors
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || err.message).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (detail.msg) {
          errorMessage = detail.msg;
        }
      }
      
      return {
        success: false,
        error: errorMessage
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
    setRoles([]);
  };

  const refreshToken = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        throw new Error('No refresh token');
      }

      const response = await apiClient.post('/api/v1/auth/refresh', {
        refresh_token: refresh
      });

      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      setToken(access_token);

      return access_token;
    } catch (error) {
      logout();
      throw error;
    }
  };

  const hasRole = (roleName) => {
    return roles.some((role) => role.role_name === roleName);
  };

  const value = {
    user,
    token,
    roles,
    loading,
    login,
    register,
    logout,
    refreshToken,
    hasRole,
    isAuthenticated: !!token
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};
