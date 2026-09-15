import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useLanguage } from '../context/LanguageContext';
import { simplifyCourseName, getSessionCategoryInfo } from '../utils/formatCourseName';

// ── Task type config (icons & colors) ────────────────────────────────────────
const TASK_THEMES = {
  university_class: { icon: '🏛️', solid: '#2563eb', dark: '#1d4ed8' },
  lecture_review:    { icon: '📖', solid: '#4f46e5', dark: '#3730a3' },
  exercise_practice: { icon: '✏️', solid: '#ea580c', dark: '#c2410c' },
  exam_preparation:  { icon: '📝', solid: '#e11d48', dark: '#be123c' },
  project_work:      { icon: '🔧', solid: '#0d9488', dark: '#0f766e' },
  reading:           { icon: '📚', solid: '#0284c7', dark: '#0369a1' },
  practice:          { icon: '🎯', solid: '#db2777', dark: '#be185d' },
};

const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  d.setDate(d.getDate() - day + (day === 0 ? -6 : 1));
  return d;
}

const WeeklyCalendarView = ({
  sessions = [],
  availabilities = [],
  onSessionClick,
  onSessionComplete,
  weekStartDate,
}) => {
  const { lang, t } = useLanguage();
  const [weekStart, setWeekStart] = useState(weekStartDate || getMonday(new Date()));

  const localeCode = lang === 'fr' ? 'fr-FR' : (lang === 'de' ? 'de-DE' : 'en-US');

  const weekDates = useMemo(() =>
    DAYS.map((_, i) => { const d = new Date(weekStart); d.setDate(d.getDate() + i); return d; }),
  [weekStart]);

  // Smart hour range
  const hours = useMemo(() => {
    const allH = sessions.flatMap(s => [
      parseInt(s.start_time), parseInt(s.end_time)
    ]);
    const min = allH.length ? Math.max(6, Math.min(...allH) - 1) : 7;
    const max = allH.length ? Math.min(22, Math.max(...allH) + 1) : 21;
    return Array.from({ length: max - min + 1 }, (_, i) => min + i);
  }, [sessions]);

  const getSlotSessions = (dayName, hour) => {
    const slotStart = `${String(hour).padStart(2,'0')}:00`;
    const slotEnd   = `${String(hour + 1).padStart(2,'0')}:00`;
    return sessions.filter(s => {
      const d = s.day || s.day_of_week;
      return d === dayName && s.start_time < slotEnd && s.end_time > slotStart;
    });
  };

  const isFirstSlot = (session, hour) =>
    parseInt(session.start_time) === hour;

  const todayStr = new Date().toDateString();
  const ROW_H = 60; // px per hour

  if (sessions.length === 0) {
    return (
      <div style={{ padding: 64, textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>📅</div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#374151', marginBottom: 8 }}>
          {t('calendar.empty_title', 'No study plan for this week')}
        </h3>
        <p style={{ color: '#6b7280', fontSize: 14, maxWidth: 450, margin: '0 auto' }}>
          {t('calendar.empty_desc', 'Click "Regenerate with AI" to create your optimized study plan.')}
        </p>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', background: '#fff', borderRadius: 12, overflow: 'hidden', border: '1px solid #e5e7eb' }}>

      {/* ── HEADER ── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '2px solid #e5e7eb',
        background: '#f9fafb',
      }}>
        {/* Title + Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#111827', textTransform: 'capitalize' }}>
            {weekDates[0].toLocaleDateString(localeCode, { month: 'long', year: 'numeric' })}
          </span>
          <span style={{
            fontSize: 12, color: '#6b7280',
            background: '#e5e7eb', borderRadius: 20, padding: '2px 10px',
          }}>
            {weekDates[0].toLocaleDateString(localeCode, { day: '2-digit', month: '2-digit' })} –{' '}
            {weekDates[6].toLocaleDateString(localeCode, { day: '2-digit', month: '2-digit' })}
          </span>
          {/* Academic & Study Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Cours Scolaires Group */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '2px 8px', borderRadius: 6, background: '#eff6ff', border: '1px solid #bfdbfe' }}>
              <span style={{ fontSize: 10, fontWeight: 800, color: '#1e40af', textTransform: 'uppercase' }}>
                🎓 {t('academic.legend_academic', 'Cours Scolaires')}:
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 10.5, color: '#1e3a8a', fontWeight: 600 }} title="Cours Magistral">
                <span style={{ width: 8, height: 8, borderRadius: 2, background: '#2563eb', display: 'inline-block' }} />
                CM
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 10.5, color: '#6d28d9', fontWeight: 600 }} title="Travaux Dirigés">
                <span style={{ width: 8, height: 8, borderRadius: 2, background: '#7c3aed', display: 'inline-block' }} />
                TD
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 10.5, color: '#047857', fontWeight: 600 }} title="Travaux Pratiques">
                <span style={{ width: 8, height: 8, borderRadius: 2, background: '#059669', display: 'inline-block' }} />
                TP
              </span>
            </div>

            {/* Study Sessions Group */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '2px 8px', borderRadius: 6, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 10, fontWeight: 800, color: '#475569', textTransform: 'uppercase' }}>
                📚 {t('academic.legend_personal', 'Travail Personnel')}:
              </span>
              {[
                { key: 'lecture_review', label: t('task.lecture_review', 'Révision'), color: '#4f46e5' },
                { key: 'exercise_practice', label: t('task.exercise_practice', 'Exercices'), color: '#ea580c' },
                { key: 'exam_preparation', label: t('task.exam_preparation', 'Prépa Exam'), color: '#e11d48' },
                { key: 'project_work', label: t('task.project_work', 'Projet'), color: '#0d9488' },
              ].map(item => (
                <span key={item.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 10.5, color: '#334155', fontWeight: 600 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: item.color, display: 'inline-block' }} />
                  {item.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Nav buttons */}
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            onClick={() => { const d = new Date(weekStart); d.setDate(d.getDate()-7); setWeekStart(d); }}
            aria-label="Previous week"
            style={{
              background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
              padding: '5px 10px', fontSize: 16, fontWeight: 700,
              color: '#374151', cursor: 'pointer', lineHeight: 1,
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#f3f4f6'}
            onMouseLeave={e => e.currentTarget.style.background = '#fff'}
          >‹</button>

          <button
            onClick={() => setWeekStart(getMonday(new Date()))}
            style={{
              background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
              padding: '5px 10px', fontSize: 12, fontWeight: 700,
              color: '#374151', cursor: 'pointer', lineHeight: 1,
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#f3f4f6'}
            onMouseLeave={e => e.currentTarget.style.background = '#fff'}
          >{t('calendar.today', 'Auj.')}</button>

          <button
            onClick={() => { const d = new Date(weekStart); d.setDate(d.getDate()+7); setWeekStart(d); }}
            aria-label="Next week"
            style={{
              background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
              padding: '5px 10px', fontSize: 16, fontWeight: 700,
              color: '#374151', cursor: 'pointer', lineHeight: 1,
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#f3f4f6'}
            onMouseLeave={e => e.currentTarget.style.background = '#fff'}
          >›</button>
        </div>
      </div>

      {/* ── GRID ── */}
      <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '72vh' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: `52px repeat(7, minmax(90px, 1fr))`,
          minWidth: 680,
        }}>

          {/* ── Day headers ── */}
          <div style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }} />
          {DAYS.map((day, i) => {
            const isToday = weekDates[i].toDateString() === todayStr;
            return (
              <div key={day} style={{
                padding: '10px 6px 8px',
                textAlign: 'center',
                background: isToday ? '#eef2ff' : '#f9fafb',
                borderLeft: '1px solid #e5e7eb',
                borderBottom: `2px solid ${isToday ? '#6366f1' : '#e5e7eb'}`,
              }}>
                <div style={{
                  fontSize: 11, fontWeight: 700, letterSpacing: 1,
                  color: isToday ? '#4f46e5' : '#9ca3af',
                  textTransform: 'uppercase', marginBottom: 4,
                }}>
                  {t(`days.short.${day}`, day.slice(0,3))}
                </div>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: 30, height: 30, borderRadius: '50%', fontSize: 14, fontWeight: 700,
                  background: isToday ? '#6366f1' : 'transparent',
                  color: isToday ? '#fff' : '#1f2937',
                }}>
                  {weekDates[i].getDate()}
                </div>
              </div>
            );
          })}

          {/* ── Time rows ── */}
          {hours.map(hour => (
            <React.Fragment key={hour}>
              {/* Hour label */}
              <div key={`h-${hour}`} style={{
                height: ROW_H, padding: '4px 8px 0 4px',
                textAlign: 'right', borderBottom: '1px solid #f3f4f6',
                background: '#fafafa', flexShrink: 0,
                position: 'sticky', left: 0, zIndex: 1,
              }}>
                <span style={{ fontSize: 11, color: '#9ca3af', fontWeight: 600 }}>
                  {String(hour).padStart(2,'0')}:00
                </span>
              </div>

              {/* Day cells */}
              {DAYS.map((day, dayIndex) => {
                const slotSessions = getSlotSessions(day, hour);
                const isToday = weekDates[dayIndex].toDateString() === todayStr;

                return (
                  <div key={`${day}-${hour}`} style={{
                    position: 'relative', height: ROW_H,
                    borderLeft: '1px solid #e5e7eb',
                    borderBottom: '1px solid #f3f4f6',
                    background: isToday ? 'rgba(99,102,241,0.03)' : '#fff',
                  }}>
                    {slotSessions.map(session => {
                      if (!isFirstSlot(session, hour)) return null;

                      const [sh, sm] = session.start_time.split(':').map(Number);
                      const [eh, em] = session.end_time.split(':').map(Number);
                      const durMin = (eh * 60 + em) - (sh * 60 + sm);
                      const heightPx = (durMin / 60) * ROW_H;
                      const topPx = (sm / 60) * ROW_H;
                      const info = getSessionCategoryInfo(session);
                      const rawTitle = session.course_name || session.subject_name || session.title || t('task.university_class', 'Cours');
                      const simplifiedTitle = simplifyCourseName(rawTitle, 24);
                      const done = session.completed;
                      const tooltipText = `${rawTitle}${session.course_code ? ` [${session.course_code}]` : ''} • ${info.fullLabel}${session.room_location ? ` • Salle: ${session.room_location}` : ''} (${session.start_time.slice(0,5)}–${session.end_time.slice(0,5)})`;

                      return (
                        <div
                          key={session.id}
                          onClick={() => onSessionClick?.(session)}
                          title={tooltipText}
                          style={{
                            position: 'absolute',
                            top: topPx + 2, left: 3, right: 3,
                            height: Math.max(heightPx - 4, 24),
                            borderRadius: 8,
                            background: done ? '#e5e7eb' : info.solid,
                            borderLeft: `3.5px solid ${done ? '#9ca3af' : info.dark}`,
                            cursor: 'pointer',
                            zIndex: 10,
                            padding: '4px 6px',
                            overflow: 'hidden',
                            boxShadow: done ? 'none' : '0 2px 7px rgba(0,0,0,0.16)',
                            opacity: done ? 0.75 : 1,
                            transition: 'transform 0.12s, box-shadow 0.12s',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'space-between',
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.transform = 'scale(1.025)';
                            e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,0,0,0.22)';
                            e.currentTarget.style.zIndex = 20;
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.transform = 'scale(1)';
                            e.currentTarget.style.boxShadow = done ? 'none' : '0 2px 7px rgba(0,0,0,0.16)';
                            e.currentTarget.style.zIndex = 10;
                          }}
                        >
                          {/* Top part: Type badge + checkmark + Title */}
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginBottom: 2 }}>
                              <span style={{
                                display: 'inline-flex', alignItems: 'center', gap: 3,
                                background: info.isCourse ? 'rgba(255,255,255,0.28)' : 'rgba(0,0,0,0.22)',
                                backdropFilter: 'blur(4px)',
                                borderRadius: 4,
                                padding: '1px 5px',
                                fontSize: 8.5,
                                fontWeight: 800,
                                letterSpacing: 0.3,
                                color: '#ffffff',
                                textTransform: 'uppercase',
                                lineHeight: 1.2,
                              }}>
                                <span>{info.icon}</span>
                                <span>{info.badgeText}</span>
                              </span>

                              {done && (
                                <span style={{
                                  background: '#10b981', color: '#fff',
                                  borderRadius: '50%', width: 13, height: 13,
                                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                  fontSize: 8, fontWeight: 900, flexShrink: 0,
                                }}>✓</span>
                              )}
                            </div>

                            {/* Simplified Course / Subject Name */}
                            <div style={{
                              fontSize: 11, fontWeight: 800, color: '#fff',
                              textDecoration: done ? 'line-through' : 'none',
                              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                              lineHeight: 1.2,
                              textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                            }}>
                              {simplifiedTitle}
                            </div>
                          </div>

                          {/* Bottom part: Time + Room if height permits */}
                          {heightPx >= 46 && (
                            <div style={{
                              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                              fontSize: 9.5, color: 'rgba(255,255,255,0.92)',
                              marginTop: 2, fontWeight: 600,
                            }}>
                              <span>{session.start_time.slice(0,5)}–{session.end_time.slice(0,5)}</span>
                              {session.room_location && (
                                <span style={{
                                  maxWidth: '48%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                  opacity: 0.95,
                                }}>
                                  📍 {session.room_location}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

WeeklyCalendarView.propTypes = {
  sessions: PropTypes.array,
  availabilities: PropTypes.array,
  constraints: PropTypes.array,
  onSessionClick: PropTypes.func,
  onSessionComplete: PropTypes.func,
  weekStartDate: PropTypes.instanceOf(Date),
};

export default WeeklyCalendarView;
