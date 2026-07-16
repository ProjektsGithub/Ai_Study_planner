import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import { AcademicDataProvider } from './context/AcademicDataContext';
import { StudyPlanProvider } from './context/StudyPlanContext';
import { GamificationProvider } from './context/GamificationContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/layout/Layout';
import HomeRedirect from './components/HomeRedirect';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import PreferencesPage from './pages/PreferencesPage';
import SubjectsPage from './pages/SubjectsPage';
import ProgressionPage from './pages/ProgressionPage';
import ExamsPage from './pages/ExamsPage';
import AvailabilitiesPage from './pages/AvailabilitiesPage';
import ConstraintsPage from './pages/ConstraintsPage';
import PlannerPage from './pages/PlannerPage';
import AIPlanPage from './pages/AIPlanPage';
import RecommendationsPage from './pages/RecommendationsPage';
import CalendarDemo from './pages/CalendarDemo';
import NotFoundPage from './pages/NotFoundPage';
import UnauthorizedPage from './pages/UnauthorizedPage';

// Admin Components
import AdminLayout from './components/layout/AdminLayout';
import ProtectedRoute from './components/ProtectedRoute';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminPlaceholder from './pages/admin/AdminPlaceholder';
import Universities from './pages/admin/Universities';
import StudyPrograms from './pages/admin/StudyPrograms';
import AcademicTracks from './pages/admin/AcademicTracks';
import Semesters from './pages/admin/Semesters';
import TeachingUnits from './pages/admin/TeachingUnits';
import Courses from './pages/admin/Courses';
import ValidationRules from './pages/admin/ValidationRules';
import BulkImport from './pages/admin/BulkImport';
import ImportHistory from './pages/admin/ImportHistory';
import AuditLogs from './pages/admin/AuditLogs';
import Reports from './pages/admin/Reports';
import RoleManagement from './pages/admin/RoleManagement';
import Settings from './pages/admin/Settings';

import './App.css';

// Initialize React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Use createBrowserRouter (data router) so useBlocker works in admin pages
const router = createBrowserRouter([
  { path: '/', element: <HomeRedirect /> },

  // Public routes
  { path: '/login',             element: <LoginPage /> },
  { path: '/register',          element: <RegisterPage /> },
  { path: '/forgot-password',   element: <ForgotPasswordPage /> },
  { path: '/reset-password',    element: <ResetPasswordPage /> },
  { path: '/demo',              element: <CalendarDemo /> },

  // Student routes — authentication required
  // ProtectedRoute (auth guard) → Layout (shell) → Page component
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { path: '/dashboard',       element: <DashboardPage /> },
          { path: '/profile',         element: <ProfilePage /> },
          { path: '/preferences',     element: <PreferencesPage /> },
          { path: '/subjects',        element: <SubjectsPage /> },
          { path: '/progression',     element: <ProgressionPage /> },
          { path: '/exams',           element: <ExamsPage /> },
          { path: '/availabilities',  element: <AvailabilitiesPage /> },
          { path: '/constraints',     element: <ConstraintsPage /> },
          { path: '/planner',         element: <PlannerPage /> },
          { path: '/ai-plan',         element: <AIPlanPage /> },
          { path: '/recommendations', element: <RecommendationsPage /> },
        ],
      },
    ],
  },

  // Admin routes — nested under /admin, guarded by ProtectedRoute
  {
    path: '/admin',
    element: (
      <ProtectedRoute allowedRoles={['super_admin', 'university_admin', 'program_coordinator']}>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true,                  element: <Navigate to="/admin/dashboard" replace /> },
      { path: 'dashboard',            element: <AdminDashboard /> },
      { path: 'universities',         element: <Universities /> },
      { path: 'programs',             element: <StudyPrograms /> },
      { path: 'tracks',               element: <AcademicTracks /> },
      { path: 'semesters',            element: <Semesters /> },
      { path: 'teaching-units',       element: <TeachingUnits /> },
      { path: 'courses',              element: <Courses /> },
      { path: 'rules',                element: <ValidationRules /> },
      { path: 'imports',              element: <BulkImport /> },
      { path: 'imports/history',      element: <ImportHistory /> },
      { path: 'reports',              element: <Reports /> },
      // Super-admin only
      {
        path: 'audit',
        element: (
          <ProtectedRoute allowedRoles={['super_admin']}>
            <AuditLogs />
          </ProtectedRoute>
        ),
      },
      {
        path: 'roles',
        element: (
          <ProtectedRoute allowedRoles={['super_admin']}>
            <RoleManagement />
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute allowedRoles={['super_admin']}>
            <Settings />
          </ProtectedRoute>
        ),
      },
    ],
  },

  // Error / fallback routes
  { path: '/unauthorized', element: <UnauthorizedPage /> },
  { path: '*',             element: <NotFoundPage /> },
]);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <AuthProvider>
          <LanguageProvider>
            <ThemeProvider>
              <AcademicDataProvider>
                <StudyPlanProvider>
                  <GamificationProvider>
                    <RouterProvider router={router} />
                  </GamificationProvider>
                </StudyPlanProvider>
              </AcademicDataProvider>
            </ThemeProvider>
          </LanguageProvider>
        </AuthProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;
