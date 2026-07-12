import { useMemo } from 'react';
import PropTypes from 'prop-types';

const TASK_CONFIG = {
  lecture_review:    { label: 'Cours',      icon: '📖', color: '#4f46e5', bg: '#f5f3ff' },
  exercise_practice: { label: 'Exercices',  icon: '✏️', color: '#c2410c', bg: '#fff7ed' },
  exam_preparation:  { label: 'Exam prep',  icon: '📝', color: '#b91c1c', bg: '#fef2f2' },
  project_work:      { label: 'Projet',     icon: '🔧', color: '#047857', bg: '#ecfdf5' },
  reading:           { label: 'Lecture',    icon: '📚', color: '#1d4ed8', bg: '#eff6ff' },
};

// ── Animated progress bar (Light Theme) ───────────────────────────────────────
function ProgressBar({ value, color, height = 6 }) {
  return (
    <div style={{
      height, borderRadius: height,
      background: '#e5e7eb', overflow: 'hidden',
    }}>
      <div style={{
        height: '100%', width: `${Math.min(100, value)}%`,
        background: color, borderRadius: height,
        transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)',
      }} />
    </div>
  );
}
ProgressBar.propTypes = { value: PropTypes.number, color: PropTypes.string, height: PropTypes.number };

// ── Main Dashboard Component (Light Theme) ────────────────────────────────────
const PlanProgressDashboard = ({ sessions = [] }) => {

  const stats = useMemo(() => {
    if (!sessions.length) return null;

    const total = sessions.length;
    const completed = sessions.filter(s => s.completed).length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    // By subject
    const bySubject = {};
    sessions.forEach(s => {
      if (!bySubject[s.subject_name]) {
        bySubject[s.subject_name] = { total: 0, completed: 0, hours: 0 };
      }
      bySubject[s.subject_name].total++;
      if (s.completed) bySubject[s.subject_name].completed++;
      // Calculate hours
      const [sh, sm] = (s.start_time || '0:0').split(':').map(Number);
      const [eh, em] = (s.end_time   || '0:0').split(':').map(Number);
      bySubject[s.subject_name].hours += (eh * 60 + em - sh * 60 - sm) / 60;
    });

    // By task type
    const byType = {};
    sessions.forEach(s => {
      const type = s.task_type || 'lecture_review';
      if (!byType[type]) byType[type] = { total: 0, completed: 0 };
      byType[type].total++;
      if (s.completed) byType[type].completed++;
    });

    // Today's sessions
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
    const todaySessions = sessions.filter(s => s.day === today);
    const todayCompleted = todaySessions.filter(s => s.completed).length;

    return { total, completed, pct, bySubject, byType, todaySessions, todayCompleted };
  }, [sessions]);

  if (!stats) {
    return (
      <div style={{
        borderRadius: 12, border: '1px solid #e5e7eb',
        background: '#f9fafb', padding: 24, textAlign: 'center',
        color: '#6b7280', fontSize: 14,
      }}>
        Génère un plan IA pour voir le suivi de progression 📊
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
      gap: 16,
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>

      {/* ── Card 1 : Progression globale ── */}
      <div style={{
        borderRadius: 12, border: '1px solid #e5e7eb',
        background: '#ffffff', padding: 20, position: 'relative', overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 16, right: 16, height: 2,
          borderRadius: '0 0 4px 4px',
          background: 'linear-gradient(90deg, #6366f1, #4f46e5)',
        }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3 style={{ color: '#111827', fontWeight: 700, fontSize: 14, margin: 0 }}>
            📊 Progression globale
          </h3>
          <span style={{
            fontSize: 26, fontWeight: 800,
            color: '#4f46e5',
          }}>{stats.pct}%</span>
        </div>

        <ProgressBar value={stats.pct} color="linear-gradient(90deg, #6366f1, #4f46e5)" height={8} />

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 12, color: '#4b5563' }}>
          <span>{stats.completed} sessions complétées</span>
          <span>{stats.total} au total</span>
        </div>

        {/* Today highlight */}
        {stats.todaySessions.length > 0 && (
          <div style={{
            marginTop: 14, padding: '10px 12px', borderRadius: 8,
            background: '#eef2ff', border: '1px solid #c7d2fe',
          }}>
            <div style={{ fontSize: 11, color: '#4f46e5', fontWeight: 700, marginBottom: 4 }}>Aujourd&apos;hui</div>
            <div style={{ fontSize: 13, color: '#1f2937', fontWeight: 600, marginBottom: 6 }}>
              {stats.todayCompleted}/{stats.todaySessions.length} sessions complétées
            </div>
            <ProgressBar
              value={stats.todaySessions.length > 0 ? (stats.todayCompleted / stats.todaySessions.length) * 100 : 0}
              color="#6366f1" height={4}
            />
          </div>
        )}
      </div>

      {/* ── Card 2 : Par type de tâche ── */}
      <div style={{
        borderRadius: 12, border: '1px solid #e5e7eb',
        background: '#ffffff', padding: 20, position: 'relative', overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 16, right: 16, height: 2,
          borderRadius: '0 0 4px 4px',
          background: 'linear-gradient(90deg, #f97316, #ea580c)',
        }} />
        <h3 style={{ color: '#111827', fontWeight: 700, fontSize: 14, margin: '0 0 14px' }}>
          🎯 Par type d&apos;activité
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {Object.entries(stats.byType).sort((a,b) => b[1].total - a[1].total).map(([type, data]) => {
            const cfg = TASK_CONFIG[type] || TASK_CONFIG.lecture_review;
            const pct = data.total > 0 ? (data.completed / data.total) * 100 : 0;
            return (
              <div key={type}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: 20, fontSize: 11,
                      background: cfg.bg, color: cfg.color, fontWeight: 700,
                    }}>{cfg.icon} {cfg.label}</span>
                  </span>
                  <span style={{ color: '#4b5563', fontWeight: 600 }}>{data.completed}/{data.total}</span>
                </div>
                <ProgressBar value={pct} color={cfg.color} height={5} />
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Card 3 : Par matière ── */}
      <div style={{
        borderRadius: 12, border: '1px solid #e5e7eb',
        background: '#ffffff', padding: 20, position: 'relative', overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 16, right: 16, height: 2,
          borderRadius: '0 0 4px 4px',
          background: 'linear-gradient(90deg, #10b981, #059669)',
        }} />
        <h3 style={{ color: '#111827', fontWeight: 700, fontSize: 14, margin: '0 0 14px' }}>
          📚 Par matière
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 220, overflowY: 'auto', paddingRight: 4 }}>
          {Object.entries(stats.bySubject)
            .sort((a, b) => b[1].total - a[1].total)
            .map(([subject, data]) => {
              const pct = data.total > 0 ? (data.completed / data.total) * 100 : 0;
              return (
                <div key={subject}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, fontSize: 12 }}>
                    <span style={{ color: '#1f2937', fontWeight: 700, maxWidth: '65%',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {subject}
                    </span>
                    <span style={{ color: '#4b5563', fontSize: 11, fontWeight: 500 }}>
                      {data.completed}/{data.total} · {data.hours.toFixed(1)}h
                    </span>
                  </div>
                  <ProgressBar value={pct} color={pct === 100 ? '#10b981' : '#3b82f6'} height={5} />
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};

PlanProgressDashboard.propTypes = {
  sessions: PropTypes.array,
  onSessionComplete: PropTypes.func,
};

export default PlanProgressDashboard;
