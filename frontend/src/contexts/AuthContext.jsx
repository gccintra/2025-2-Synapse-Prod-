import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { usersAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext deve ser usado dentro do AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const response = await usersAPI.getUserProfile();
      if (response.success && response.data) {
        setUser(response.data);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.log('Auth check failed:', error.message);

      // Se for erro 401, definitivamente não está autenticado
      if (error.status === 401 || error.isAuthError) {
        console.log('Token inválido ou expirado');
      }

      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    try {
      await usersAPI.logout();
    } catch (error) {
      console.error('Logout API failed:', error);
    } finally {
      // Sempre limpa o estado, mesmo se a API falhar
      setUser(null);
      setIsAuthenticated(false);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const response = await usersAPI.getUserProfile();
      if (response.success && response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error('Profile refresh failed:', error);
      // Se falhar ao refreshar, pode ser que o token expirou
      setUser(null);
      setIsAuthenticated(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshProfile,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};