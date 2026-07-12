import { useState, useEffect, useMemo, useCallback } from 'react';
import { useStudyPlan } from '../context/StudyPlanContext';
import { useAcademicData } from '../context/AcademicDataContext';
import WeeklyCalendarView from '../components/WeeklyCalendarView';
import SessionEditor from '../components/SessionEditor';
import PlanProgressDashboard from '../components/PlanProgressDashboard';
import apiClient from '../api/client';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Skeleton from '../components/ui/Skeleton';

const AIPlanPage = () => {
  const {
    currentPlan,
    loading: planLoading,
    generating,
    generationProgress,
    error: planError,
    fetchCurrentPlan,
    generatePlan,
    regeneratePlan,
    addSession,
    updateSession,
    deleteSession
  } = useStudyPlan();

  const { subjects, loading: academicLoading } = useAcademicData();

  const [availabilities, setAvailabilities] = useState([]);
  const [constraints, setConstraints] = useState([]);
  const [loadingExtras, setLoadingExtras] = useState(false);
  const [error, setError] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  // Local session list for optimistic completion updates
  const [localSessions, setLocalSessions] = useState([]);
  
  // Local state for week start date (Monday of the selected week)
  const [weekStartDate, setWeekStartDate] = useState(() => getMonday(new Date()));

  useEffect(() => {
    loadExtras();
  }, []);

  // Sync localSessions when plan changes
  useEffect(() => {
    setLocalSessions(currentPlan?.sessions || []);
  }, [currentPlan]);

  const loadExtras = async () => {
    setLoadingExtras(true);
    try {
      const [availRes, constRes] = await Promise.all([
        apiClient.get('/api/v1/availabilities').catch(() => ({ data: { availabilities: [] } })),
        apiClient.get('/api/v1/constraints').catch(() => ({ data: { constraints: [] } })),
      ]);
      setAvailabilities(availRes.data?.availabilities || []);
      setConstraints(constRes.data?.constraints || []);
    } catch (err) {
      console.error('Error loading planner extras:', err);
      setError('Error loading schedule preferences');
    } finally {
      setLoadingExtras(false);
    }
  };

  const handleGeneratePlan = async (force = false) => {
    setError(null);
    try {
      // Use local date to avoid UTC timezone shift (toISOString converts to UTC)
      const weekStartStr = `${weekStartDate.getFullYear()}-${String(weekStartDate.getMonth() + 1).padStart(2, '0')}-${String(weekStartDate.getDate()).padStart(2, '0')}`;
      await generatePlan(weekStartStr, force);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e) => e.msg || e.message || JSON.stringify(e)).join(', '));
      } else {
        setError(typeof detail === 'string' ? detail : 'Error generating study plan with AI');
      }
    }
  };

  const handleRegeneratePlan = async () => {
    setError(null);
    try {
      await regeneratePlan('manual_edit', null, 'Global regeneration request');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e) => e.msg || e.message || JSON.stringify(e)).join(', '));
      } else {
        setError(typeof detail === 'string' ? detail : 'Error regenerating study plan');
      }
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

  const handleCloseEditor = () => {
    setIsEditorOpen(false);
    setSelectedSession(null);
  };

  const handleSaveSession = async (sessionData) => {
    if (!currentPlan) return;
    
    setError(null);
    try {
      if (selectedSession) {
        await updateSession(currentPlan.id || currentPlan.plan_id, selectedSession.id, sessionData);
      } else {
        await addSession(currentPlan.id || currentPlan.plan_id, sessionData);
      }
      handleCloseEditor();
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Error saving study session');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!currentPlan) return;
    
    setError(null);
    try {
      await deleteSession(currentPlan.id || currentPlan.plan_id, sessionId);
      handleCloseEditor();
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Error deleting study session');
    }
  };

  // Helper to calculate start of the week
  function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
  }

  const sessions = localSessions.length > 0 ? localSessions : (currentPlan?.sessions || []);
  const isLoading = planLoading || academicLoading || loadingExtras;

  // Mark session as complete (optimistic update)
  const handleSessionComplete = useCallback(async (session) => {
    if (!currentPlan) return;
    // Optimistic update
    setLocalSessions(prev => prev.map(s =>
      s.id === session.id ? { ...s, completed: true } : s
    ));
    try {
      await apiClient.post(`/api/v1/study-plans/${currentPlan.plan_id}/sessions/${session.id}/complete`);
    } catch (err) {
      // Revert on error
      console.error('Failed to mark session complete:', err);
      setLocalSessions(prev => prev.map(s =>
        s.id === session.id ? { ...s, completed: false } : s
      ));
    }
  }, [currentPlan]);

  const totalStudyHours = useMemo(() => {
    return sessions.reduce((acc, s) => {
      const [sh, sm] = s.start_time.split(':').map(Number);
      const [eh, em] = s.end_time.split(':').map(Number);
      return acc + (eh * 60 + em - (sh * 60 + sm)) / 60;
    }, 0);
  }, [sessions]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">

      {/* ── Generation Overlay ── */}
      {generating && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9000,
          background: 'rgba(10,10,20,0.85)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            background: 'rgba(15,15,30,0.95)', border: '1px solid rgba(99,102,241,0.4)',
            borderRadius: 24, padding: '40px 48px', maxWidth: 420, width: '90%',
            textAlign: 'center', boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
          }}>
            {/* Pulsing brain icon */}
            <div style={{
              width: 80, height: 80, borderRadius: '50%', margin: '0 auto 24px',
              background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(79,70,229,0.2))',
              border: '2px solid rgba(99,102,241,0.5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 36,
              animation: 'pulse 2s ease-in-out infinite',
            }}>🧠</div>

            <h2 style={{ color: '#fff', fontWeight: 800, fontSize: 20, marginBottom: 8 }}>
              {currentPlan ? 'Régénération en cours...' : 'Génération en cours...'}
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, marginBottom: 28 }}>
              L&apos;IA analyse tes matières et contraintes pour créer ton planning optimal.
              Cela peut prendre <strong style={{ color: '#a78bfa' }}>30 à 90 secondes</strong>.
            </p>

            {/* Steps */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 28 }}>
              {[
                {
                  key: 'preparing',
                  icon: '⚙️',
                  label: 'Préparation des données...',
                  done: ['generating', 'running', 'saving', 'done'].includes(generationProgress),
                  active: generationProgress === 'preparing',
                },
                {
                  key: 'running',
                  icon: '✨',
                  label: 'IA génère le planning en temps réel...',
                  done: ['saving', 'done'].includes(generationProgress),
                  active: ['generating', 'generating_batch', 'running'].includes(generationProgress),
                },
                {
                  key: 'saving',
                  icon: '💾',
                  label: 'Sauvegarde du planning...',
                  done: generationProgress === 'done',
                  active: generationProgress === 'saving',
                },
              ].map((step) => {
                const isActive = step.active;
                const isDone   = step.done;
                return (
                  <div key={step.key} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '10px 14px', borderRadius: 10,
                    background: isDone ? 'rgba(16,185,129,0.12)' : isActive ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${isDone ? 'rgba(16,185,129,0.3)' : isActive ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.06)'}`,
                    transition: 'all 0.3s ease',
                  }}>
                    <span style={{ fontSize: 16 }}>{isDone ? '✅' : step.icon}</span>
                    <span style={{
                      fontSize: 13, fontWeight: 500,
                      color: isDone ? '#34d399' : isActive ? '#a78bfa' : 'rgba(255,255,255,0.35)',
                    }}>{step.label}</span>
                    {isActive && (
                      <span style={{ marginLeft: 'auto', display: 'flex', gap: 3 }}>
                        {[0,1,2].map(d => (
                          <span key={d} style={{
                            width: 5, height: 5, borderRadius: '50%', background: '#818cf8',
                            display: 'inline-block',
                            animation: 'bounce 1.2s ease-in-out infinite',
                            animationDelay: `${d * 0.2}s`,
                          }} />
                        ))}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div style={{ height: 4, borderRadius: 4, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 4,
                background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                width: generationProgress === 'pending' ? '15%'
                     : generationProgress === 'running' ? '60%'
                     : generationProgress === 'done'    ? '95%' : '5%',
                transition: 'width 0.8s ease',
              }} />
            </div>
            <style>{`
              @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.05);opacity:0.8} }
              @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-5px)} }
            `}</style>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <span>AI Study Plan</span>
            <Badge variant="info">Model: Llama-3-8B-Study-LoRA</Badge>
          </h1>
          {currentPlan && (
            <p className="text-white/40 text-sm mt-1">
              Generated on {new Date(currentPlan.created_at || currentPlan.generation_timestamp).toLocaleString('en-US')}
              {currentPlan.edited && (
                <span className="ml-2 px-2 py-0.5 rounded text-xs bg-violet-500/20 text-violet-300 border border-violet-500/30">
                  Manually Edited
                </span>
              )}
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="secondary"
            onClick={handleAddSession}
            disabled={!currentPlan || isLoading}
          >
            <svg className="w-4 h-4 mr-1.5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Add Session
          </Button>

          <Button
            variant="primary"
            onClick={() => currentPlan ? handleRegeneratePlan() : handleGeneratePlan()}
            disabled={generating || isLoading}
          >
            {generating ? (
              <>
                <svg className="animate-spin w-4 h-4 mr-1.5 inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {generationProgress === 'pending' && 'En file d\'attente...'}
                {generationProgress === 'running' && 'IA en cours de génération...'}
                {(!generationProgress || generationProgress === 'done') && 'Finalisation...'}
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-1.5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                {currentPlan ? 'Regenerate with AI' : 'Generate AI Study Plan'}
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Error notification */}
      {(error || planError) && (
        <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-start gap-3">
          <svg className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-red-300">{error || (typeof planError === 'string' ? planError : planError?.message) || 'An error occurred'}</p>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && !currentPlan && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-10 w-32" />
            </div>
            <div className="p-6 space-y-4">
              <Skeleton className="h-96 w-full" />
            </div>
          </Card>
        </div>
      )}

      {/* No Plan State */}
      {!isLoading && !currentPlan && (
        <Card className="text-center py-16 px-4">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-violet-500/10 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">
              📅
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No Active Study Plan</h3>
            <p className="text-white/60 mb-6">
              Let our AI design an optimized weekly study plan tailored for your courses and upcoming exams.
            </p>
            <Button
              variant="primary"
              onClick={() => handleGeneratePlan(true)}
              disabled={generating}
            >
              Generate My AI Plan
            </Button>
          </div>
        </Card>
      )}

      {/* Calendar and Stats */}
      {currentPlan && !isLoading && (
        <div className="space-y-6">
          <div className="rounded-2xl overflow-hidden shadow-lg">
            <WeeklyCalendarView
              sessions={sessions}
              availabilities={availabilities}
              constraints={constraints}
              onSessionClick={handleSessionClick}
              onSessionComplete={handleSessionComplete}
              weekStartDate={weekStartDate}
            />
          </div>

          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="relative rounded-2xl border border-white/10 bg-gradient-to-br from-violet-600/20 to-violet-600/5 backdrop-blur-md p-5 overflow-hidden">
              <div className="absolute top-0 left-4 right-4 h-0.5 rounded-b-full bg-gradient-to-r from-violet-500 to-violet-400 opacity-60" />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-white/40 mb-1.5">Study Volume</p>
                  <p className="text-3xl font-bold text-white">{totalStudyHours.toFixed(1)}h</p>
                </div>
                <span className="text-3xl opacity-60">⏱</span>
              </div>
            </div>

            <div className="relative rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-600/20 to-cyan-600/5 backdrop-blur-md p-5 overflow-hidden">
              <div className="absolute top-0 left-4 right-4 h-0.5 rounded-b-full bg-gradient-to-r from-cyan-500 to-cyan-400 opacity-60" />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-white/40 mb-1.5">Work Sessions</p>
                  <p className="text-3xl font-bold text-white">{sessions.length}</p>
                </div>
                <span className="text-3xl opacity-60">📋</span>
              </div>
            </div>

            <div className="relative rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-600/20 to-emerald-600/5 backdrop-blur-md p-5 overflow-hidden">
              <div className="absolute top-0 left-4 right-4 h-0.5 rounded-b-full bg-gradient-to-r from-emerald-500 to-emerald-400 opacity-60" />
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-white/40 mb-1.5">Affected Subjects</p>
                  <p className="text-3xl font-bold text-white">
                    {new Set(sessions.map((s) => s.subject_id)).size}
                  </p>
                </div>
                <span className="text-3xl opacity-60">📚</span>
              </div>
            </div>
          </div>

          {/* Progress Dashboard */}
          <div>
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span>📊</span> Suivi de progression
            </h2>
            <PlanProgressDashboard
              sessions={sessions}
              onSessionComplete={handleSessionComplete}
            />
          </div>
        </div>
      )}

      {/* Session Modal Editor */}
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

export default AIPlanPage;
