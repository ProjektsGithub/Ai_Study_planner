import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * HomeRedirect Component
 * Redirects to dashboard if authenticated, otherwise to login
 */
const HomeRedirect = () => {
  const { isAuthenticated, loading } = useAuth();

  // Show nothing while checking auth status
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  // Redirect based on authentication status
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
};

export default HomeRedirect;
