/**
 * Auth Context Provider
 * 
 * Managed User Authentication State für die gesamte App.
 * 
 * Features:
 * - Login/Logout
 * - User State Management
 * - Token Storage (localStorage)
 * - Auto-Login (Token persistence)
 * - Protected Route Logic
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User, login as apiLogin, logout as apiLogout, getCurrentUser, set401Handler } from '../api/client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
  handle401Error: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Handle 401 Unauthorized - automatischer Logout und Redirect
  const handle401Error = () => {
    console.warn('401 Unauthorized detected - logging out user');
    setUser(null);
    localStorage.removeItem('auth_token');
    
    // Nur zur Login-Page redirecten wenn wir nicht schon dort sind
    if (location.pathname !== '/login') {
      navigate('/login', { 
        replace: true,
        state: { message: 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.' }
      });
    }
  };

  // Registriere den 401-Handler beim API-Client
  useEffect(() => {
    set401Handler(handle401Error);
  }, [location.pathname]);

  // Check if user is already logged in (on app load)
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Versuche User aus Token zu holen
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        // Token ist invalid/abgelaufen oder nicht vorhanden
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      setLoading(true);

      // Login API Call (speichert Token automatisch in localStorage)
      await apiLogin(username, password);

      // Hole User Daten
      const currentUser = await getCurrentUser();
      setUser(currentUser);

    } catch (err: any) {
      const errorMessage = err.message || 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      await apiLogout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    logout,
    refreshUser,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    handle401Error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth Hook
 * 
 * Usage:
 *   const { user, login, logout, isAuthenticated, isAdmin } = useAuth();
 */
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}
