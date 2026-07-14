import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import apiClient from '../api/client';
import { useAuth } from './AuthContext';
import { useCrossBrowserSync } from '../hooks/useCrossBrowserSync';

const StudyPlanContext = createContext(null);

export const useStudyPlan = () => {
  const context = useContext(StudyPlanContext);
  if (!context) {
    throw new Error('useStudyPlan must be used within StudyPlanProvider');
  }
  return context;
};

export const StudyPlanProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [currentPlan, setCurrentPlan] = useState(null);
  const [planHistory, setPlanHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const [generationProgress, setGenerationProgress] = useState(null); // null | "pending" | "running"

  const fetchCurrentPlan = useCallback(async () => {
    if (!isAuthenticated) return null;
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/v1/study-plans/current');
      setCurrentPlan(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching current study plan:', err);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e) => e.msg || e.message || JSON.stringify(e)).join(', '));
      } else if (detail && typeof detail === 'string') {
        setError(detail);
      } else {
        setError(err.message || 'Error fetching study plan');
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Cross-tab synchronization: Listen for updates from other tabs
  const handleCrossTabMessage = useCallback((data) => {
    if (data.action === 'STUDY_PLAN_UPDATED') {
      console.log('📡 Received update notification from another tab, refreshing...');
      fetchCurrentPlan();
    }
  }, [fetchCurrentPlan]);

  const { broadcast } = useCrossBrowserSync('study_plan_sync', handleCrossTabMessage);

  const fetchPlanHistory = useCallback(async (page = 1) => {
    if (!isAuthenticated) return;
    try {
      const res = await apiClient.get(`/api/v1/study-plans/history?page=${page}`);
      setPlanHistory(res.data?.plans || []);
    } catch (err) {
      console.error('Error fetching study plan history:', err);
    }
  }, [isAuthenticated]);

  /**
   * generatePlan — SSE streaming (nouveau)
   * POST /study-plans/stream → SSE events token par token
   * Pas de polling, pas de timeout
   */
  const generatePlan = async (weekStart, forceRegenerate = false) => {
    setGenerating(true);
    setGenerationProgress('preparing');
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

      const response = await fetch(`${baseURL}/api/v1/study-plans/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ week_start: weekStart, force_regenerate: forceRegenerate }),
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody?.detail || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let resultPlan = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;

          let evt;
          try { evt = JSON.parse(raw); } catch { continue; }

          if (evt.type === 'status') {
            setGenerationProgress(evt.status);
          } else if (evt.type === 'token') {
            setGenerationProgress('running');
          } else if (evt.type === 'done') {
            resultPlan = evt.plan;
            setGenerationProgress('done');
            await fetchCurrentPlan();
            
            // Notify other tabs
            broadcast({ action: 'STUDY_PLAN_UPDATED' });
            return resultPlan;
          } else if (evt.type === 'error') {
            throw new Error(evt.message || 'AI generation failed');
          }
        }
      }

      if (!resultPlan) {
        throw new Error('La génération n\'a produit aucun plan');
      }
      return resultPlan;

    } catch (err) {
      console.error('Error generating study plan:', err);
      throw err;
    } finally {
      setGenerating(false);
      setGenerationProgress(null);
    }
  };


  const regeneratePlan = async () => {
    // Réutilise generatePlan avec force_regenerate=true
    // Le backend /stream gère déjà la suppression du plan existant
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    const monday = new Date(today);
    monday.setDate(today.getDate() + daysToMonday);
    const weekStart = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, '0')}-${String(monday.getDate()).padStart(2, '0')}`;

    return generatePlan(weekStart, true);
  };

  const markSessionComplete = async (sessionId) => {
    try {
      await apiClient.post('/api/v1/study-plans/complete-session', {
        session_id: sessionId
      });
      await fetchCurrentPlan();
      
      // Notify other tabs
      broadcast({ action: 'STUDY_PLAN_UPDATED' });
    } catch (err) {
      console.error('Error completing session:', err);
      throw err;
    }
  };

  const addSession = async (planId, sessionData) => {
    try {
      const res = await apiClient.post(`/api/v1/study-plans/${planId}/sessions`, sessionData);
      await fetchCurrentPlan();
      
      // Notify other tabs
      broadcast({ action: 'STUDY_PLAN_UPDATED' });
      return res.data;
    } catch (err) {
      console.error('Error adding session:', err);
      throw err;
    }
  };

  const updateSession = async (planId, sessionId, sessionData) => {
    try {
      const res = await apiClient.put(`/api/v1/study-plans/${planId}/sessions/${sessionId}`, sessionData);
      await fetchCurrentPlan();
      
      // Notify other tabs
      broadcast({ action: 'STUDY_PLAN_UPDATED' });
      return res.data;
    } catch (err) {
      console.error('Error updating session:', err);
      throw err;
    }
  };

  const deleteSession = async (planId, sessionId) => {
    try {
      await apiClient.delete(`/api/v1/study-plans/${planId}/sessions/${sessionId}`);
      await fetchCurrentPlan();
      
      // Notify other tabs
      broadcast({ action: 'STUDY_PLAN_UPDATED' });
    } catch (err) {
      console.error('Error deleting session:', err);
      throw err;
    }
  };

  useEffect(() => {
    fetchCurrentPlan();
    fetchPlanHistory();
  }, [fetchCurrentPlan, fetchPlanHistory]);

  const value = {
    currentPlan,
    planHistory,
    loading,
    generating,
    generationProgress,
    error,
    fetchCurrentPlan,
    fetchPlanHistory,
    generatePlan,
    regeneratePlan,
    markSessionComplete,
    addSession,
    updateSession,
    deleteSession
  };

  return <StudyPlanContext.Provider value={value}>{children}</StudyPlanContext.Provider>;
};

StudyPlanProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
