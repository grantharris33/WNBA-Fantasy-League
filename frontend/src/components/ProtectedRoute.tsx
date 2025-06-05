import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Show loading indicator while checking auth status
    return (
      <div className="min-h-screen bg-slate-50 flex justify-center items-center" style={{fontFamily: 'Manrope, "Noto Sans", sans-serif'}}>
        <div className="flex flex-col items-center bg-white/80 backdrop-blur-sm rounded-xl p-8 shadow-lg">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0c7ff2] mb-4"></div>
          <p className="text-slate-600 font-medium">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  // Render children routes if authenticated
  return <Outlet />;
};

export default ProtectedRoute;