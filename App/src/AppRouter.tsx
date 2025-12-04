/**
 * App Router Setup
 * 
 * Definiert alle Routes der Application:
 * - /login (public)
 * - /admin (protected - admin only)
 * - / (protected - main app)
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { AdminPanel } from './pages/AdminPanel';
import { MappingTool } from './pages/MappingTool';
import { EnvTest } from './pages/EnvTest';
import App from './App';

export function AppRouter() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}
