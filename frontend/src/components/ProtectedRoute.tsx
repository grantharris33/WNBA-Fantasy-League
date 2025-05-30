import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NavBar from './layout/NavBar';
import React from 'react';

export const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Show loading indicator while checking auth status
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Render children routes if authenticated
  return (
    <>
      <NavBar />
      <div className="container mx-auto mt-4 p-4">
        <Outlet />
      </div>
    </>
  );
};

export default ProtectedRoute;