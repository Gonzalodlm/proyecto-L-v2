import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { User } from '../types';
import { api, tokenManager } from '../services/api';

// Auth State
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth Actions
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: User }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; payload: Partial<User> };

// Initial state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };
    default:
      return state;
  }
}

// Auth Context
interface AuthContextType {
  state: AuthState;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  updateProfile: (data: { first_name?: string; last_name?: string }) => Promise<boolean>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth Provider
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = tokenManager.getToken();
    if (!token) {
      dispatch({ type: 'AUTH_ERROR', payload: 'No token found' });
      return;
    }

    try {
      dispatch({ type: 'AUTH_START' });
      const response = await api.auth.getProfile();
      
      if (response.success && response.data) {
        dispatch({ type: 'AUTH_SUCCESS', payload: response.data as User });
      } else {
        tokenManager.clearTokens();
        dispatch({ type: 'AUTH_ERROR', payload: response.error || 'Authentication failed' });
      }
    } catch (error) {
      tokenManager.clearTokens();
      dispatch({ type: 'AUTH_ERROR', payload: 'Authentication check failed' });
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      dispatch({ type: 'AUTH_START' });
      const response = await api.auth.login(email, password);
      
      if (response.success && response.data) {
        const { user, access_token, refresh_token } = response.data;
        
        tokenManager.setToken(access_token);
        tokenManager.setRefreshToken(refresh_token);
        
        dispatch({ type: 'AUTH_SUCCESS', payload: user as User });
        return true;
      } else {
        dispatch({ type: 'AUTH_ERROR', payload: response.error || 'Login failed' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: 'Login failed' });
      return false;
    }
  };

  const register = async (
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ): Promise<boolean> => {
    try {
      dispatch({ type: 'AUTH_START' });
      const response = await api.auth.register(email, password, firstName, lastName);
      
      if (response.success && response.data) {
        const { user, access_token, refresh_token } = response.data;
        
        tokenManager.setToken(access_token);
        tokenManager.setRefreshToken(refresh_token);
        
        dispatch({ type: 'AUTH_SUCCESS', payload: user as User });
        return true;
      } else {
        dispatch({ type: 'AUTH_ERROR', payload: response.error || 'Registration failed' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: 'Registration failed' });
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await api.auth.logout();
    } catch (error) {
      // Ignore logout API errors
    } finally {
      tokenManager.clearTokens();
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const updateProfile = async (data: { first_name?: string; last_name?: string }): Promise<boolean> => {
    try {
      const response = await api.auth.updateProfile(data);
      
      if (response.success && response.data) {
        dispatch({ type: 'UPDATE_USER', payload: response.data as Partial<User> });
        return true;
      } else {
        dispatch({ type: 'AUTH_ERROR', payload: response.error || 'Profile update failed' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: 'Profile update failed' });
      return false;
    }
  };

  const changePassword = async (currentPassword: string, newPassword: string): Promise<boolean> => {
    try {
      const response = await api.auth.changePassword(currentPassword, newPassword);
      
      if (response.success) {
        return true;
      } else {
        dispatch({ type: 'AUTH_ERROR', payload: response.error || 'Password change failed' });
        return false;
      }
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: 'Password change failed' });
      return false;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    state,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    clearError,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}