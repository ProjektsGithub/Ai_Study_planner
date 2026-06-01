import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import Card from '../components/ui/Card';

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [upcomingSessions, setUpcomingSessions] = useState([]);
  const [stats, setStats] = useState({
    totalSubjects: 0,
    totalAvailabilities: 0,
    totalConstraints: 0,
    weeklyGoal: 0
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load current plan
      const plansResponse = await apiClient.get('/api/v1/study-plans/current');
      if (plansResponse.data) {
        const plan = plansResponse.data;
        setCurrentPlan(plan);

        // Load sessions for current plan
        const sessionsResponse = await apiClient.get(`/api/v1/study-plans/${plan.id}/sessions`);
        const sessions = sessionsResponse.data || [];
        
        // Filter upcoming sessions (today and future)
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        
        const upcoming = sessions
          .filter(session => {
            const sessionDate = new Date(session.date);
            return sessionDate >= today;
          })
          .sort((a, b) => new Date(a.date) - new Date(b.date))
          .slice(0, 5);
        
        setUpcomingSessions(upcoming);
      }

      // Load stats
      const [subjectsRes, availabilitiesRes, constraintsRes, profileRes] = await Promise.all([
        apiClient.get('/api/v1/subjects'),
        apiClient.get('/api/v1/availabilities'),
        apiClient.get('/api/v1/constraints'),
        apiClient.get('/api/v1/profile').catch(() => ({ data: null })) // Profile might not exist yet
      ]);

      setStats({
        totalSubjects: subjectsRes.data?.subjects?.length || 0,
        totalAvailabilities: availabilitiesRes.data?.availabilities?.length || 0,
        totalConstraints: constraintsRes.data?.constraints?.length || 0,
        weeklyGoal: profileRes.data?.weekly_study_goal || 0
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatTime = (timeString) => {
    return timeString.substring(0, 5);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="mt-2 text-gray-600">Vue d'ensemble de votre planning d'étude</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-100 rounded-lg p-3">
              <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Matières</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalSubjects}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-100 rounded-lg p-3">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Disponibilités</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalAvailabilities}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-yellow-100 rounded-lg p-3">
              <svg className="w-8 h-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Contraintes</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalConstraints}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-purple-100 rounded-lg p-3">
              <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Objectif hebdo</p>
              <p className="text-2xl font-bold text-gray-900">{stats.weeklyGoal}h</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Current Plan */}
        <Card>
          <div className="mb-4">
            <h2 className="text-xl font-bold text-gray-900">Plan actuel</h2>
          </div>
          {currentPlan ? (
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-600">Semaine du</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatDate(currentPlan.week_start_date)}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  currentPlan.status === 'active' ? 'bg-green-100 text-green-800' :
                  currentPlan.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {currentPlan.status === 'active' ? 'Actif' :
                   currentPlan.status === 'completed' ? 'Terminé' : 'Brouillon'}
                </span>
              </div>
              
              <div className="pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Heures totales</p>
                    <p className="text-2xl font-bold text-gray-900">{currentPlan.total_hours}h</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">{currentPlan.session_count}</p>
                  </div>
                </div>
              </div>

              <div className="pt-4">
                <Link
                  to="/planner"
                  className="block w-full text-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Voir le planning
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun plan</h3>
              <p className="mt-1 text-sm text-gray-500">Créez votre premier planning d'étude</p>
              <div className="mt-6">
                <Link
                  to="/planner"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Créer un plan
                </Link>
              </div>
            </div>
          )}
        </Card>

        {/* Upcoming Sessions */}
        <Card>
          <div className="mb-4">
            <h2 className="text-xl font-bold text-gray-900">Prochaines sessions</h2>
          </div>
          {upcomingSessions.length > 0 ? (
            <div className="space-y-3">
              {upcomingSessions.map((session) => (
                <div
                  key={session.id}
                  className="flex items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-gray-900">{session.subject_name}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {formatDate(session.date)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatTime(session.start_time)} - {formatTime(session.end_time)}
                      {' '}({session.duration_hours}h)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune session</h3>
              <p className="mt-1 text-sm text-gray-500">Vos prochaines sessions apparaîtront ici</p>
            </div>
          )}
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Actions rapides</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/subjects"
            className="flex items-center p-4 bg-white rounded-lg shadow border border-gray-200 hover:border-blue-500 transition-colors"
          >
            <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <div className="ml-4">
              <p className="font-medium text-gray-900">Ajouter une matière</p>
              <p className="text-sm text-gray-600">Gérer vos matières</p>
            </div>
          </Link>

          <Link
            to="/availabilities"
            className="flex items-center p-4 bg-white rounded-lg shadow border border-gray-200 hover:border-blue-500 transition-colors"
          >
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-4">
              <p className="font-medium text-gray-900">Définir disponibilités</p>
              <p className="text-sm text-gray-600">Configurer vos horaires</p>
            </div>
          </Link>

          <Link
            to="/planner"
            className="flex items-center p-4 bg-white rounded-lg shadow border border-gray-200 hover:border-blue-500 transition-colors"
          >
            <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <div className="ml-4">
              <p className="font-medium text-gray-900">Générer un plan</p>
              <p className="text-sm text-gray-600">Créer votre planning</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
