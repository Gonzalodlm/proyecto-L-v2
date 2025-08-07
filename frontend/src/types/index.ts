// Core types for the application

export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  has_risk_profile: boolean;
  has_portfolio: boolean;
}

export interface RiskProfile {
  id: number;
  user_id: number;
  questionnaire_answers: QuestionnaireAnswers;
  total_score: number;
  risk_bucket: number;
  risk_label: string;
  risk_description: string;
  created_at: string;
  is_active: boolean;
}

export interface QuestionnaireAnswers {
  age: number;
  horizon: string;
  income: string;
  knowledge: string;
  max_drop: string;
  reaction: string;
  liquidity: string;
  goal: string;
  inflation: string;
  digital: string;
}

export interface Portfolio {
  id: number;
  user_id: number;
  risk_profile_id: number;
  allocations: Record<string, number>;
  allocation_breakdown: AllocationBreakdown[];
  initial_investment?: number;
  is_balanced: boolean;
  total_allocation: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  last_rebalance?: string;
  // Performance metrics
  current_value?: number;
  total_return_pct?: number;
  annual_return_pct?: number;
  volatility_pct?: number;
  sharpe_ratio?: number;
  max_drawdown_pct?: number;
}

export interface AllocationBreakdown {
  ticker: string;
  weight: number;
  weight_pct: number;
  etf_info: ETFInfo;
}

export interface ETFInfo {
  ticker: string;
  nombre: string;
  descripcion: string;
  tipo: string;
  riesgo: string;
  rendimiento_esperado: string;
  expense_ratio?: string;
  aum?: string;
  inception_date?: string;
  color: string;
  [key: string]: any; // For additional ETF-specific properties
}

export interface DiversificationAnalysis {
  score: number;
  breakdown: Record<string, number>;
  total_assets: number;
  max_concentration: number;
  recommendations: string[];
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  count?: number;
  validation_errors?: string[];
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface QuestionnaireForm extends QuestionnaireAnswers {}

// Navigation and UI types
export interface NavItem {
  label: string;
  path: string;
  icon?: React.ComponentType;
  protected?: boolean;
}

export interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  format?: 'currency' | 'percentage' | 'number';
  icon?: React.ComponentType;
}

// Chart data types
export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface PortfolioChartData {
  portfolio: ChartDataPoint[];
  benchmarks?: Record<string, ChartDataPoint[]>;
}

// Constants
export const RISK_BUCKETS = {
  0: { label: 'Conservador', color: '#4CAF50', description: 'Prioriza preservación del capital' },
  1: { label: 'Moderado', color: '#2196F3', description: 'Balance entre seguridad y crecimiento' },
  2: { label: 'Balanceado', color: '#FF9800', description: 'Distribución equilibrada' },
  3: { label: 'Crecimiento', color: '#FF5722', description: 'Enfocado en crecimiento largo plazo' },
  4: { label: 'Agresivo', color: '#9C27B0', description: 'Máximo crecimiento, alta volatilidad' },
} as const;

export const ETF_COLORS = {
  BIL: '#2E7D32',
  AGG: '#1976D2',
  ACWI: '#388E3C',
  VNQ: '#F57C00',
  GLD: '#FFD700',
} as const;

export type RiskBucket = keyof typeof RISK_BUCKETS;
export type ETFTicker = keyof typeof ETF_COLORS;