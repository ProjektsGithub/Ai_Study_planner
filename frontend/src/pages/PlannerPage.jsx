import { useState, useEffect } from 'react';
import WeeklyCalendarView from '../components/WeeklyCalendarView';
import SessionEditor from '../components/SessionEditor';
import { useStudyPlan } from '../context/StudyPlanContext';
import apiClient from '../api/client';

const PlannerPage = () => {
  // Use StudyPlanContext instead of local state
  const {
    currentPlan: studyPlan,
    loading: planLoading,
    generating,
    generationProgress,
    error: planError,
    generatePlan,
    addSession,
    updateSession,
    deleteSession
  } = useStudyPlan();

  const [availabilities, setAvailabilities] = useState([]);
  const [constraints, setConstraints] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  // Derive sessions from studyPlan
  const sessions = studyPlan?.sessions || [];

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Note: studyPlan is now loaded via StudyPlanContext
      // We only need to load availabilities, constraints, and subjects
      const [availRes, constRes, subRes] = await Promise.all([
        apiClient.get('/api/v1/availabilities'),
        apiClient.get('/api/v1/constraints'),
        apiClient.get('/api/v1/subjects'),
      ]);
      setAvailabilities(availRes.data?.availabilities || []);
      setConstraints(constRes.data?.constraints || []);
      setSubjects(subRes.data?.subjects || []);
    } catch (err) {
      console.error('Error loading data:', err);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e) => e.msg || e.message || JSON.stringify(e)).join(', '));
      } else if (detail && typeof detail === 'object') {
        setError(JSON.stringify(detail));
      } else {
        setError(detail || 'Erreur lors du chargement des données');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    console.log('🚀 Starting plan generation (SSE streaming)...');
    setError(null);

    try {
      const today = new Date();
      const dayOfWeek = today.getDay();
      const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const monday = new Date(today);
      monday.setDate(today.getDate() + daysToMonday);
      const weekStart = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, '0')}-${String(monday.getDate()).padStart(2, '0')}`;

      // Use Context's generatePlan method
      await generatePlan(weekStart, true);
      console.log('✅ Plan generated successfully');
    } catch (err) {
      console.error('❌ Error generating plan:', err);
      setError(err.message || 'Erreur lors de la génération du plan');
    } finally {
      console.log('🏁 Plan generation finished');
    }
  };

  const handleSessionClick = (session) => { setSelectedSession(session); setIsEditorOpen(true); };
  const handleAddSession = () => { setSelectedSession(null); setIsEditorOpen(true); };
  const handleCloseEditor = () => { setIsEditorOpen(false); setSelectedSession(null); };

  const handleSaveSession = async (sessionData) => {
    if (!studyPlan) throw new Error("Aucun plan d'étude actif");
    
    // Use plan_id (UUID) instead of id
    const planId = studyPlan.plan_id || studyPlan.id;
    if (!planId) {
      throw new Error("Plan ID is missing");
    }
    
    try {
      if (selectedSession) {
        // Update existing session via Context
        await updateSession(planId, selectedSession.id, sessionData);
      } else {
        // Add new session via Context
        await addSession(planId, sessionData);
      }
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message || 'Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!studyPlan) throw new Error("Aucun plan d'étude actif");
    
    // Use plan_id (UUID) instead of id
    const planId = studyPlan.plan_id || studyPlan.id;
    if (!planId) {
      throw new Error("Plan ID is missing");
    }
    
    try {
      await deleteSession(planId, sessionId);
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message || 'Erreur lors de la suppression');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white">Study Planner</h1>
          {studyPlan && (
            <p className="text-slate-400 dark:text-white/40 text-sm mt-1">
              Plan created on {new Date(studyPlan.created_at).toLocaleDateString('en-US')}
              {studyPlan.edited && <span className="ml-2 text-violet-600 dark:text-violet-400">· edited</span>}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleAddSession}
            disabled={!studyPlan || loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-emerald-200 text-emerald-700 bg-white hover:bg-emerald-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-semibold shadow-sm dark:border-emerald-500/40 dark:text-emerald-300 dark:bg-transparent dark:hover:bg-emerald-500/10"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Add Session
          </button>
          <button
            onClick={handleGeneratePlan}
            disabled={generating || loading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 text-white text-sm font-semibold shadow-sm hover:shadow-glow-violet hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none transition-all"
          >
            {generating ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {generatingStatus === 'running' ? 'IA en cours...' : 'En attente...'}
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                {studyPlan ? 'Regenerate' : 'Generate AI Plan'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {(error || planError) && (
        <div className="mb-6 rounded-xl bg-red-50 border border-red-200 p-4 flex items-start gap-3 dark:bg-red-500/10 dark:border-red-500/20">
          <svg className="h-5 w-5 text-red-550 dark:text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-red-805 dark:text-red-300">{error || planError}</p>
        </div>
      )}

      {/* AI Generation progress banner */}
      {generating && (
        <div className="mb-6 rounded-xl border border-violet-250 bg-violet-50 p-4 dark:border-violet-500/30 dark:bg-violet-500/10">
          <div className="flex items-center gap-3">
            <div className="relative flex-shrink-0">
              <div className="w-8 h-8 rounded-full border-2 border-violet-200 border-t-violet-600 animate-spin dark:border-violet-500/20 dark:border-t-violet-400" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs">🧠</span>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-violet-800 dark:text-violet-300">
                {generationProgress === 'preparing' && 'Préparation des données...'}
                {generationProgress === 'running' && "L'IA écrit votre planning en temps réel..."}
                {generationProgress === 'saving' && 'Sauvegarde du planning...'}
                {generationProgress === 'done' && 'Planning généré avec succès !'}
                {!generationProgress && 'Initialisation...'}
              </p>
              <p className="text-xs text-violet-650 dark:text-violet-400/70 mt-0.5">
                {generationProgress === 'preparing' && 'Chargement de vos matières, créneaux et contraintes.'}
                {generationProgress === 'running' && 'Llama 3.1-8B génère sur A100'}
                {generationProgress === 'saving' && 'Enregistrement en base de données...'}
                {generationProgress === 'done' && 'Le planning est maintenant disponible.'}
              </p>
            </div>
            <div className="flex gap-1 flex-shrink-0">
              <span className="w-1.5 h-1.5 bg-violet-500 dark:bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-violet-500 dark:bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-violet-500 dark:bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {(loading || planLoading) && !studyPlan && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-400 dark:text-white/40 text-sm">Loading study plan...</p>
          </div>
        </div>
      )}

      {/* Calendar */}
      {!loading && !planLoading && (
        <div className="rounded-2xl border border-slate-100 bg-white shadow-sm overflow-hidden mb-6 dark:border-white/10 dark:bg-white/[0.03]">
          <WeeklyCalendarView
            sessions={sessions}
            availabilities={availabilities}
            constraints={constraints}
            onSessionClick={handleSessionClick}
          />
        </div>
      )}

      {/* Stats */}
      {studyPlan && sessions.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              label: 'Total Hours',
              value: `${studyPlan.total_hours?.toFixed(1) || '0.0'}h`,
              icon: '⏱',
              gradient: 'from-violet-50 to-violet-50/30 dark:from-violet-600/25 dark:to-violet-600/5',
              topBar: 'from-violet-500 to-violet-400',
            },
            {
              label: 'Sessions',
              value: sessions.length,
              icon: '📋',
              gradient: 'from-cyan-50 to-cyan-50/30 dark:from-cyan-600/25 dark:to-cyan-600/5',
              topBar: 'from-cyan-500 to-cyan-400',
            },
            {
              label: 'Subjects',
              value: new Set(sessions.map((s) => s.subject_id)).size,
              icon: '📚',
              gradient: 'from-emerald-50 to-emerald-50/30 dark:from-emerald-600/25 dark:to-emerald-600/5',
              topBar: 'from-emerald-500 to-emerald-400',
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className={`relative rounded-2xl border border-slate-100 bg-gradient-to-br ${stat.gradient} p-5 overflow-hidden shadow-sm dark:border-white/10`}
            >
              <div className={`absolute top-0 left-4 right-4 h-0.5 rounded-b-full bg-gradient-to-r ${stat.topBar} opacity-60`} />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400 dark:text-white/40 mb-1.5">{stat.label}</p>
                  <p className="text-3xl font-bold text-slate-800 dark:text-white">{stat.value}</p>
                </div>
                <span className="text-3xl opacity-60">{stat.icon}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Session Editor */}
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
