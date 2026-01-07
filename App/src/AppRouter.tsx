/**
 * App Router Setup
 * 
 * Definiert alle Routes der Application:
 * - /login (public)
 * - /admin (protected - admin only)
 * - / (protected - main app)
 */

import React from 'react';
import { HashRouter, BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { AdminPanel } from './pages/AdminPanel';
import { ProductLifecycle } from './pages/ProductLifecycle';
import { MappingTool } from './pages/MappingTool';
import { EnvTest } from './pages/EnvTest';
import App from './App';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

// Detect if running in Electron (file:// protocol)
const isElectron = window.location.protocol === 'file:';
const Router = isElectron ? HashRouter : BrowserRouter;

export function AppRouter() {
  return (
    <Router>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/env-test" element={<EnvTest />} />

          {/* Admin-Only Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin={true}>
                <AdminPanel />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lifecycle"
            element={
              <ProtectedRoute requireAdmin={true}>
                <ProductLifecycle />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mapping-tool"
            element={
              <ProtectedRoute requireAdmin={true}>
                <MappingTool />
              </ProtectedRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <App />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </QueryClientProvider>
    </Router>
  );
}
