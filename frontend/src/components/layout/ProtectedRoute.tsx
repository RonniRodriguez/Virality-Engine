import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../services/authStore';

export const ProtectedRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login but save the location they tried to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
