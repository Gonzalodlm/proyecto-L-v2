import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse } from '../types';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'impulso_access_token';
const REFRESH_TOKEN_KEY = 'impulso_refresh_token';

export const tokenManager = {
  getToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  removeToken: (): void => localStorage.removeItem(TOKEN_KEY),
  
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setRefreshToken: (token: string): void => localStorage.setItem(REFRESH_TOKEN_KEY, token),
  removeRefreshToken: (): void => localStorage.removeItem(REFRESH_TOKEN_KEY),
  
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = tokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          });
          
          const { access_token } = response.data.data;
          tokenManager.setToken(access_token);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          tokenManager.clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        tokenManager.clearTokens();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Generic API request wrapper
async function apiRequest<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  endpoint: string,
  data?: any
): Promise<ApiResponse<T>> {
  try {
    const response: AxiosResponse<ApiResponse<T>> = await apiClient.request({
      method,
      url: endpoint,
      data,
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Handle API error responses
      const apiError = error.response?.data as ApiResponse;
      if (apiError && !apiError.success) {
        return apiError;
      }
      
      // Handle network/timeout errors
      return {
        success: false,
        error: error.message || 'Error de conexión',
      };
    }
    
    // Handle unexpected errors
    return {
      success: false,
      error: 'Error inesperado',
    };
  }
}

// API service methods
export const api = {
  // Auth endpoints
  auth: {
    login: (email: string, password: string) =>
      apiRequest<{ user: any; access_token: string; refresh_token: string }>('POST', '/api/auth/login', {
        email,
        password,
      }),
    
    register: (email: string, password: string, first_name?: string, last_name?: string) =>
      apiRequest<{ user: any; access_token: string; refresh_token: string }>('POST', '/api/auth/register', {
        email,
        password,
        first_name,
        last_name,
      }),
    
    refresh: () => apiRequest<{ access_token: string }>('POST', '/api/auth/refresh'),
    
    logout: () => apiRequest('DELETE', '/api/auth/logout'),
    
    getProfile: () => apiRequest('GET', '/api/auth/profile'),
    
    updateProfile: (data: { first_name?: string; last_name?: string }) =>
      apiRequest('PUT', '/api/auth/profile', data),
    
    changePassword: (currentPassword: string, newPassword: string) =>
      apiRequest('POST', '/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }),
    
    verifyToken: () => apiRequest('GET', '/api/auth/verify-token'),
  },

  // ETFs endpoints
  etfs: {
    getAll: () => apiRequest('GET', '/api/etfs'),
    
    getById: (ticker: string) => apiRequest('GET', `/api/etfs/${ticker}`),
    
    getByType: (type: string) => apiRequest('GET', `/api/etfs/filter/type/${type}`),
    
    getByRisk: (risk: string) => apiRequest('GET', `/api/etfs/filter/risk/${risk}`),
    
    validateAllocation: (allocations: Record<string, number>) =>
      apiRequest('POST', '/api/etfs/validate', { allocations }),
    
    analyzeDiversification: (allocations: Record<string, number>) =>
      apiRequest('POST', '/api/etfs/diversification', { allocations }),
    
    getSupportedTickers: () => apiRequest<string[]>('GET', '/api/etfs/tickers'),
  },

  // Analysis endpoints
  analysis: {
    createRiskProfile: (answers: Record<string, any>) =>
      apiRequest('POST', '/api/analysis/risk-profile', { answers }),
    
    getCurrentRiskProfile: () => apiRequest('GET', '/api/analysis/risk-profile'),
    
    getRiskProfileHistory: () => apiRequest('GET', '/api/analysis/risk-profile/history'),
    
    simulateScore: (answers: Record<string, any>) =>
      apiRequest('POST', '/api/analysis/simulate-score', { answers }),
    
    getQuestionnaireStructure: () => apiRequest('GET', '/api/analysis/questionnaire/structure'),
  },

  // Portfolios endpoints
  portfolios: {
    getAll: () => apiRequest('GET', '/api/portfolios'),
    
    getById: (id: number) => apiRequest('GET', `/api/portfolios/${id}`),
    
    create: (data: {
      risk_profile_id?: number;
      allocations?: Record<string, number>;
      initial_investment?: number;
    }) => apiRequest('POST', '/api/portfolios', data),
    
    update: (id: number, data: {
      allocations?: Record<string, number>;
      initial_investment?: number;
    }) => apiRequest('PUT', `/api/portfolios/${id}`, data),
    
    delete: (id: number) => apiRequest('DELETE', `/api/portfolios/${id}`),
    
    getCurrent: () => apiRequest('GET', '/api/portfolios/current'),
    
    getModel: (riskBucket: number) => apiRequest('GET', `/api/portfolios/model/${riskBucket}`),
    
    getRebalanceSuggestions: (id: number) =>
      apiRequest('GET', `/api/portfolios/${id}/rebalance`),
    
    updatePerformance: (id: number, metrics: Record<string, number>) =>
      apiRequest('POST', `/api/portfolios/${id}/performance`, metrics),
    
    compare: (portfolios: Array<{ name: string; allocations: Record<string, number> }>) =>
      apiRequest('POST', '/api/portfolios/compare', { portfolios }),
  },
};

export default api;