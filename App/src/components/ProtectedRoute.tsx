/**
 * Protected Route Component
 * 
 * Schützt Routes vor unauthentifizierten Zugriffen.
 * Redirected zu /login wenn User nicht eingeloggt ist.
 * 
 * Optional: requireAdmin für Admin-only Routes
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactElement;
  requireAdmin?: boolean;
}

export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Zeige Loading während Auth Check
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  // Nicht eingeloggt -> Redirect zu /login
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Admin-Route aber kein Admin -> Forbidden
  if (requireAdmin && user.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <h1 className="text-2xl font-bold text-red-600">403 - Forbidden</h1>
        <p className="text-gray-600">You don't have permission to access this page.</p>
      </div>
    );
  }

  // Alles OK -> Render children
  return children;
}
