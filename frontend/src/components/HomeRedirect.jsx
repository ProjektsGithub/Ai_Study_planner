import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * HomeRedirect Component
 * Redirects to the correct dashboard based on the user's role:
 * - super_admin / university_admin / program_coordinator → /admin/dashboard
 * - students and unauthenticated users → /dashboard or /login
 */
const ADMIN_ROLES = ['super_admin', 'university_admin', 'program_coordinator'];

const HomeRedirect = () => {
  const { isAuthenticated, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-violet-500"></div>
          <p className="mt-4 text-white/40">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Admin roles → admin dashboard
  const isAdmin = ADMIN_ROLES.some((role) => hasRole(role));
  return <Navigate to={isAdmin ? '/admin/dashboard' : '/dashboard'} replace />;
};

export default HomeRedirect;
