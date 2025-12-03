import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';
import { toast } from 'react-toastify';

const PrivateRoute = () => {
  const { isAuthenticated, loading } = useAuthContext();

  // Mostrar loading enquanto verifica autenticação
  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    toast.info("Please log in to access this page.");
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default PrivateRoute;
