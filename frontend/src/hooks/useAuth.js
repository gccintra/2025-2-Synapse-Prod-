// hooks/useAuth.js (ou onde estiver seu hook)
import { useState, useEffect } from 'react';
import { usersAPI } from '../services/api'; // Ajuste o caminho da importação

export const useAuth = () => {
  // Começa como null (carregando) para não chutar nem true nem false
  const [isAuthenticated, setIsAuthenticated] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Tenta bater na rota protegida
        await usersAPI.getUserProfile();
        setIsAuthenticated(true);
      } catch (error) {
        // Se der erro (401), não está logado
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  // Retorna loading enquanto isAuthenticated for null
  return { 
    isAuthenticated: !!isAuthenticated, 
    loading: isAuthenticated === null 
  };
};