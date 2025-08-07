import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { RiskAssessmentPage } from './pages/profile/RiskAssessmentPage';
import { Layout } from './components/layout/Layout';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { state } = useAuth();

  if (state.isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Cargando...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!state.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Simple Dashboard Component (placeholder)
function DashboardPage() {
  const { state } = useAuth();

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            ¡Bienvenido a Impulso Inversor!
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Hola {state.user?.first_name || state.user?.email}
          </p>
          
          {!state.user?.has_risk_profile && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-2xl mx-auto">
              <h2 className="text-xl font-semibold text-blue-900 mb-4">
                🎯 Empezar tu Análisis de Inversión
              </h2>
              <p className="text-blue-800 mb-6">
                Para crear tu portafolio personalizado, primero necesitamos conocer tu perfil de riesgo.
                Este análisis toma solo 5 minutos.
              </p>
              <a href="/risk-assessment">
                <button className="bg-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-600 transition-colors">
                  Hacer Análisis de Riesgo
                </button>
              </a>
            </div>
          )}

          {state.user?.has_risk_profile && !state.user?.has_portfolio && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-2xl mx-auto">
              <h2 className="text-xl font-semibold text-green-900 mb-4">
                📊 Perfil de Riesgo Completado
              </h2>
              <p className="text-green-800 mb-6">
                ¡Excelente! Ahora puedes crear tu portafolio personalizado basado en tu perfil.
              </p>
              <button className="bg-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-600 transition-colors">
                Crear Mi Portafolio
              </button>
            </div>
          )}

          {state.user?.has_risk_profile && state.user?.has_portfolio && (
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 max-w-2xl mx-auto">
              <h2 className="text-xl font-semibold text-primary-900 mb-4">
                ✅ Todo Listo
              </h2>
              <p className="text-primary-800 mb-6">
                Tu portafolio está configurado y listo. Puedes ver su rendimiento y hacer ajustes.
              </p>
              <button className="bg-primary-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-600 transition-colors">
                Ver Mi Portafolio
              </button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

// Main App Component
function AppContent() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/risk-assessment"
          element={
            <ProtectedRoute>
              <RiskAssessmentPage />
            </ProtectedRoute>
          }
        />
        
        {/* Redirect root to appropriate page */}
        <Route
          path="/"
          element={<Navigate to="/dashboard" replace />}
        />
        
        {/* Catch all - redirect to dashboard */}
        <Route
          path="*"
          element={<Navigate to="/dashboard" replace />}
        />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;