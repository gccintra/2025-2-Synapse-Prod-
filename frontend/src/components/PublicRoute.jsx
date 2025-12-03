import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';

const PublicRoute = () => {
  const { isAuthenticated, loading } = useAuthContext();

  // Mostrar loading enquanto verifica autenticação
  if (loading) {
    return <div>Loading...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/feed" replace />;
  }

  return <Outlet />;
};

export default PublicRoute;
