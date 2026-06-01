import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/layout/Layout';
import HomeRedirect from './components/HomeRedirect';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import SubjectsPage from './pages/SubjectsPage';
import AvailabilitiesPage from './pages/AvailabilitiesPage';
import ConstraintsPage from './pages/ConstraintsPage';
import PlannerPage from './pages/PlannerPage';
import CalendarDemo from './pages/CalendarDemo';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Home route - redirects based on auth status */}
            <Route path="/" element={<HomeRedirect />} />
            
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/demo" element={<CalendarDemo />} />
            
            {/* Protected routes with layout */}
            <Route path="/dashboard" element={<Layout><DashboardPage /></Layout>} />
            <Route path="/profile" element={<Layout><ProfilePage /></Layout>} />
            <Route path="/subjects" element={<Layout><SubjectsPage /></Layout>} />
            <Route path="/availabilities" element={<Layout><AvailabilitiesPage /></Layout>} />
            <Route path="/constraints" element={<Layout><ConstraintsPage /></Layout>} />
            <Route path="/planner" element={<Layout><PlannerPage /></Layout>} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
