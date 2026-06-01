import { useState, useEffect } from 'react';
import WeeklyCalendarView from '../components/WeeklyCalendarView';
import SessionEditor from '../components/SessionEditor';
import axios from 'axios';

/**
 * PlannerPage Component
 * Main page for viewing and managing study plans
 */
const PlannerPage = () => {
  const [studyPlan, setStudyPlan] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [availabilities, setAvailabilities] = useState([]);
  const [constraints, setConstraints] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Session editor state
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  // API base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load current study plan
      const planResponse = await axios.get(`${API_BASE_URL}/api/v1/study-plans/current`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (planResponse.data) {
        setStudyPlan(planResponse.data);
        setSessions(planResponse.data.sessions || []);
      }

      // Load availabilities
      const availResponse = await axios.get(`${API_BASE_URL}/api/v1/availabilities`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setAvailabilities(availResponse.data || []);

      // Load constraints
      const constraintsResponse = await axios.get(`${API_BASE_URL}/api/v1/constraints`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setConstraints(constraintsResponse.data || []);

      // Load subjects
      const subjectsResponse = await axios.get(`${API_BASE_URL}/api/v1/subjects`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setSubjects(subjectsResponse.data || []);

    } catch (err) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.detail || 'Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get the Monday of the current week
      const today = new Date();
      const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
      const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // If Sunday, go back 6 days
      const monday = new Date(today);
      monday.setDate(today.getDate() + daysToMonday);
      
      // Format as YYYY-MM-DD
      const weekStart = monday.toISOString().split('T')[0];

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/study-plans/generate`,
        {
          week_start: weekStart,
          force_regenerate: false
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      setStudyPlan(response.data);
      setSessions(response.data.sessions || []);
      
      // Show success message
      alert('Plan d\'étude généré avec succès !');
    } catch (err) {
      console.error('Error generating plan:', err);
      
      // Handle different error formats
      let errorMessage = 'Erreur lors de la génération du plan';
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        
        // If detail is an array of validation errors
        if (Array.isArray(detail)) {
          errorMessage = detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail);
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionClick = (session) => {
    setSelectedSession(session);
    setIsEditorOpen(true);
  };

  const handleAddSession = () => {
    setSelectedSession(null);
    setIsEditorOpen(true);
  };

  const handleSaveSession = async (sessionData) => {
    if (!studyPlan) {
      throw new Error('Aucun plan d\'étude actif');
    }

    try {
      if (selectedSession) {
        // Update existing session
        const response = await axios.put(
          `${API_BASE_URL}/api/v1/study-plans/${studyPlan.id}/sessions/${selectedSession.id}`,
          sessionData,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        
        // Update sessions list
        setSessions(prev => 
          prev.map(s => s.id === selectedSession.id ? response.data : s)
        );
      } else {
        // Create new session
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/study-plans/${studyPlan.id}/sessions`,
          sessionData,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        
        // Add new session to list
        setSessions(prev => [...prev, response.data]);
      }

      // Mark plan as edited
      setStudyPlan(prev => ({ ...prev, edited: true }));
      
    } catch (err) {
      console.error('Error saving session:', err);
      throw new Error(err.response?.data?.detail || 'Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!studyPlan) {
      throw new Error('Aucun plan d\'étude actif');
    }

    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/study-plans/${studyPlan.id}/sessions/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      
      // Remove session from list
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // Mark plan as edited
      setStudyPlan(prev => ({ ...prev, edited: true }));
      
    } catch (err) {
      console.error('Error deleting session:', err);
      throw new Error(err.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleCloseEditor = () => {
    setIsEditorOpen(false);
    setSelectedSession(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Planificateur d'Études
              </h1>
              {studyPlan && (
                <p className="text-sm text-gray-600 mt-1">
                  Plan créé le {new Date(studyPlan.created_at).toLocaleDateString('fr-FR')}
                  {studyPlan.edited && <span className="ml-2 text-blue-600">(modifié)</span>}
                </p>
              )}
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleAddSession}
                disabled={!studyPlan || loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                + Ajouter une session
              </button>
              <button
                onClick={handleGeneratePlan}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Génération...' : studyPlan ? 'Régénérer' : 'Générer un plan'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && !studyPlan && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Chargement...</p>
            </div>
          </div>
        )}

        {/* Calendar view */}
        {!loading && (
          <WeeklyCalendarView
            sessions={sessions}
            availabilities={availabilities}
            constraints={constraints}
            onSessionClick={handleSessionClick}
          />
        )}

        {/* Statistics */}
        {studyPlan && sessions.length > 0 && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total d'heures</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {studyPlan.total_hours?.toFixed(1) || '0.0'}h
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Sessions</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {sessions.length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-purple-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Matières</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {new Set(sessions.map(s => s.subject_id)).size}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Session Editor Modal */}
      <SessionEditor
        session={selectedSession}
        subjects={subjects}
        onSave={handleSaveSession}
        onDelete={handleDeleteSession}
        onClose={handleCloseEditor}
        isOpen={isEditorOpen}
      />
    </div>
  );
};

export default PlannerPage;
