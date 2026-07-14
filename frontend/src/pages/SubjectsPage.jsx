import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

// ─── Status config ────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  in_progress: {
    label: 'In Progress',
    color: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30',
    textColor: 'text-blue-700 dark:text-blue-300',
    dot: 'bg-blue-500 dark:bg-blue-400',
    ring: 'ring-blue-500/20 dark:ring-blue-500/40',
    icon: '🔵',
    aiHint: 'In planning',
  },
  validated: {
    label: 'Validated ✓',
    color: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-300 dark:border-emerald-500/30',
    textColor: 'text-emerald-700 dark:text-emerald-300',
    dot: 'bg-emerald-500 dark:bg-emerald-400',
    ring: 'ring-emerald-500/20 dark:ring-emerald-500/40',
    icon: '✅',
    aiHint: 'Excluded',
  },
  retake: {
    label: 'Retake ⚠',
    color: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/30',
    textColor: 'text-amber-700 dark:text-amber-300',
    dot: 'bg-amber-500 dark:bg-amber-400',
    ring: 'ring-amber-500/20 dark:ring-amber-500/40',
    icon: '⚠️',
    aiHint: 'High priority',
  },
  optional: {
    label: 'Optional',
    color: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/20 dark:text-purple-300 dark:border-purple-500/30',
    textColor: 'text-purple-700 dark:text-purple-300',
    dot: 'bg-purple-500 dark:bg-purple-400',
    ring: 'ring-purple-500/20 dark:ring-purple-500/40',
    icon: '⚙️',
    aiHint: 'Optional',
  },
};

// ─── Difficulty stars ─────────────────────────────────────────────────────────
const DifficultyStars = ({ level }) => (
  <span className="flex gap-0.5">
    {[1, 2, 3, 4, 5].map((i) => (
      <span
        key={i}
        className={`text-[10px] ${i <= level ? 'text-violet-500 dark:text-violet-400' : 'text-slate-200 dark:text-white/10'}`}
      >
        ★
      </span>
    ))}
  </span>
);

// ─── Status dropdown (Portal-based to escape overflow-hidden parents) ─────────
const StatusDropdown = ({ courseId, currentStatus, onStatusChange, saving }) => {
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState({});
  const btnRef = useRef(null);
  const cfg = currentStatus ? STATUS_CONFIG[currentStatus] : null;

  const handleToggle = () => {
    if (!open && btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const menuHeight = 230; // approx height of the menu
      const spaceBelow = viewportHeight - rect.bottom;
      const showAbove = spaceBelow < menuHeight && rect.top > menuHeight;

      setMenuStyle({
        position: 'fixed',
        minWidth: Math.max(rect.width, 210) + 'px',
        right: (window.innerWidth - rect.right) + 'px',
        ...(showAbove
          ? { bottom: (window.innerHeight - rect.top + 4) + 'px' }
          : { top: (rect.bottom + 4) + 'px' }
        ),
        zIndex: 9999,
      });
    }
    setOpen((v) => !v);
  };

  const menu = open ? (
    <>
      {/* Backdrop to close on outside click */}
      <div className="fixed inset-0" style={{ zIndex: 9998 }} onClick={() => setOpen(false)} />
      <div
        style={menuStyle}
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl shadow-2xl overflow-hidden"
      >
        {/* Not selected option */}
        <button
          onClick={() => { onStatusChange(courseId, null); setOpen(false); }}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-xs text-slate-500 dark:text-white/40 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
        >
          <span className="w-2 h-2 rounded-full bg-slate-300 dark:bg-white/20" />
          Not selected
          <span className="ml-auto text-slate-400 dark:text-white/20 text-[10px]">clear</span>
        </button>
        <div className="h-px bg-slate-100 dark:bg-white/5 mx-3" />
        {Object.entries(STATUS_CONFIG).map(([key, c]) => (
          <button
            key={key}
            onClick={() => { onStatusChange(courseId, key); setOpen(false); }}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-xs hover:bg-slate-50 dark:hover:bg-white/5 transition-colors
              ${currentStatus === key ? 'bg-slate-50 dark:bg-white/5' : ''}
            `}
          >
            <span className={`w-2 h-2 rounded-full ${c.dot}`} />
            <span className={c.textColor}>{c.label}</span>
            <span className="ml-auto text-slate-400 dark:text-white/25 text-[10px]">{c.aiHint}</span>
          </button>
        ))}
      </div>
    </>
  ) : null;

  return (
    <div className="relative">
      <button
        ref={btnRef}
        id={`status-btn-${courseId}`}
        onClick={handleToggle}
        disabled={saving}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold
          transition-all duration-150 min-w-[140px] justify-between
          ${cfg
            ? `${cfg.color} ${cfg.ring} ring-1`
            : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300 dark:bg-white/5 dark:border-white/10 dark:text-white/40 dark:hover:border-white/20'
          }
          ${saving ? 'opacity-50 cursor-wait' : 'cursor-pointer hover:opacity-90'}
        `}
      >
        <span>{cfg ? cfg.label : 'Not selected'}</span>
        <svg
          className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {createPortal(menu, document.body)}
    </div>
  );
};

// ─── Course row ───────────────────────────────────────────────────────────────
const CourseRow = ({ course, onStatusChange, savingId }) => {
  const cfg = course.enrollment_status ? STATUS_CONFIG[course.enrollment_status] : null;

  return (
    <div
      id={`course-row-${course.id}`}
      className={`
        flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200
        border group
        ${cfg
          ? `bg-slate-50/50 border-slate-100 hover:bg-slate-50 dark:bg-white/[0.03] dark:border-white/8 dark:hover:bg-white/[0.05]`
          : 'bg-transparent border-transparent hover:bg-slate-50/30 hover:border-slate-100 dark:hover:bg-white/[0.02] dark:hover:border-white/5'
        }
      `}
    >
      {/* Status indicator line */}
      <div className={`w-1 h-8 rounded-full flex-shrink-0 transition-colors
        ${cfg ? cfg.dot : 'bg-slate-200 dark:bg-white/10'}`}
      />

      {/* Course info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-slate-900 dark:text-white truncate">{course.name}</span>
          {course.code && (
            <span className="text-[10px] font-mono text-slate-600 bg-slate-100 dark:text-slate-400 dark:bg-slate-800 px-1.5 py-0.5 rounded">
              {course.code}
            </span>
          )}
          {/* Retake badge (German Wiederholung) */}
          {course.is_retake && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <span>⚠</span> Rattrapage S{course.retake_semester_number}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-[11px] text-violet-600 dark:text-violet-400 font-semibold">{course.ects_credits} ECTS</span>
          <span className="text-slate-400 dark:text-slate-500 text-[10px]">·</span>
          <span className="text-[11px] text-slate-600 dark:text-slate-400">coeff. {course.coefficient}</span>
          <span className="text-slate-400 dark:text-slate-500 text-[10px]">·</span>
          <DifficultyStars level={course.difficulty_level} />
        </div>
      </div>

      {/* Status dropdown */}
      <StatusDropdown
        courseId={course.id}
        currentStatus={course.enrollment_status}
        onStatusChange={onStatusChange}
        saving={savingId === course.id}
      />
    </div>
  );
};

// ─── Teaching Unit group card ─────────────────────────────────────────────────
const TeachingUnitGroup = ({ tuName, tuCode, tuEcts, courses, onStatusChange, savingId }) => {
  const [collapsed, setCollapsed] = useState(false);
  const enrolled = courses.filter((c) => c.enrollment_status).length;

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-2xl bg-white dark:bg-slate-900 shadow-sm">
      {/* Header */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="w-full flex items-center gap-3 px-5 py-4 bg-slate-50/50 hover:bg-slate-50 dark:bg-slate-800/50 dark:hover:bg-slate-800 transition-colors text-left rounded-t-2xl"
      >
        <svg
          className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform flex-shrink-0 ${collapsed ? '-rotate-90' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-900 dark:text-white">{tuName}</span>
            {tuCode && (
              <span className="text-[10px] font-mono text-slate-600 bg-slate-100 dark:text-slate-400 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                {tuCode}
              </span>
            )}
          </div>
          {tuEcts && (
            <span className="text-[11px] text-slate-600 dark:text-slate-400">{tuEcts} ECTS required</span>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold
            ${enrolled === courses.length
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
              : enrolled > 0
                ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
            }`}
          >
            {enrolled}/{courses.length}
          </span>
        </div>
      </button>

      {/* Courses */}
      {!collapsed && (
        <div className="p-2 space-y-1 bg-white dark:bg-slate-900/50 rounded-b-2xl">
          {courses.map((c) => (
            <CourseRow
              key={c.id}
              course={c}
              onStatusChange={onStatusChange}
              savingId={savingId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
const SubjectsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingId, setSavingId] = useState(null);
  const [filter, setFilter] = useState('all'); // all | pending | in_progress | retake | validated
  const navigate = useNavigate();

  const loadCourses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/v1/enrollments/my-courses');
      setData(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to load courses.';
      setError({ message: detail, status: err.response?.status });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  // Auto-save when status changes
  const handleStatusChange = useCallback(async (courseId, newStatus) => {
    setSavingId(courseId);
    try {
      // Find the course to get its enrollment_id if it exists
      const course = data?.courses?.find(c => c.id === courseId);
      
      if (newStatus === null) {
        // Remove enrollment - need to find enrollment_id first
        if (course?.enrollment_id) {
          await apiClient.delete(`/api/v1/enrollments/${course.enrollment_id}`);
        }
        // If no enrollment_id exists, nothing to delete (already not enrolled)
      } else {
        // Upsert enrollment
        await apiClient.post('/api/v1/enrollments', {
          course_id: courseId,
          status: newStatus,
        });
      }
      // Optimistic update
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          courses: prev.courses.map((c) =>
            c.id === courseId
              ? { ...c, enrollment_status: newStatus }
              : c
          ),
          enrolled_courses: prev.courses.filter(
            (c) => (c.id === courseId ? newStatus !== null : c.enrollment_status !== null)
          ).length,
        };
      });
    } catch (err) {
      console.error('Failed to save enrollment:', err);
      alert(`Failed to update course status: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSavingId(null);
    }
  }, [data]);

  // ── Filtered courses ────────────────────────────────────────────────────────
  const filteredCourses = data?.courses?.filter((c) => {
    if (filter === 'all') return true;
    if (filter === 'pending') return !c.enrollment_status;
    return c.enrollment_status === filter;
  }) ?? [];

  // Group by teaching unit — only NON-retake courses
  const groups = filteredCourses
    .filter(c => !c.is_retake)
    .reduce((acc, course) => {
      const key = course.teaching_unit_id ?? '__none__';
      if (!acc[key]) {
        acc[key] = { tu: course.teaching_unit, courses: [] };
      }
      acc[key].courses.push(course);
      return acc;
    }, {});

  // Group retake courses by retake_semester_number
  const retakeGroups = filteredCourses
    .filter(c => c.is_retake)
    .reduce((acc, course) => {
      const semKey = `retake_s${course.retake_semester_number}`;
      if (!acc[semKey]) {
        acc[semKey] = {
          semNumber: course.retake_semester_number,
          tuGroups: {},
        };
      }
      const tuKey = course.teaching_unit_id ?? '__none__';
      if (!acc[semKey].tuGroups[tuKey]) {
        acc[semKey].tuGroups[tuKey] = { tu: course.teaching_unit, courses: [] };
      }
      acc[semKey].tuGroups[tuKey].courses.push(course);
      return acc;
    }, {});

  const hasRetakeCourses = Object.keys(retakeGroups).length > 0;

  // ── Stats ───────────────────────────────────────────────────────────────────
  const total = data?.total_courses ?? 0;
  const enrolled = data?.courses?.filter((c) => c.enrollment_status).length ?? 0;
  const retakeCount = data?.courses?.filter((c) => c.enrollment_status === 'retake').length ?? 0;
  const validatedCount = data?.courses?.filter((c) => c.enrollment_status === 'validated').length ?? 0;
  const totalEcts = data?.courses?.reduce((s, c) => s + c.ects_credits, 0) ?? 0;
  const enrolledEcts = data?.courses
    ?.filter((c) => c.enrollment_status && c.enrollment_status !== 'validated')
    ?.reduce((s, c) => s + c.ects_credits, 0) ?? 0;

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
      </div>
    );
  }

  // ── Error / Onboarding ──────────────────────────────────────────────────────
  if (error) {
    const isSetupRequired = error.status === 400 || error.status === 404;
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-16 text-center animate-slide-up">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-violet-600/20 to-indigo-500/20 border border-violet-500/20 flex items-center justify-center text-4xl">
          {isSetupRequired ? '📚' : '⚠️'}
        </div>
        <h2 className="text-2xl font-bold text-white mb-3">
          {isSetupRequired ? 'Academic Profile Needed' : 'Something went wrong'}
        </h2>
        <p className="text-white/50 mb-8 leading-relaxed">{error.message}</p>
        {isSetupRequired ? (
          <Link
            to="/preferences"
            className="inline-flex items-center gap-2 px-6 py-3 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-xl transition-colors shadow-glow-sm"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Go to Preferences
          </Link>
        ) : (
          <button
            onClick={loadCourses}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-xl transition-colors border border-white/10"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  // ── Main render ─────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">

      {/* ── Header ── */}
      <div className="mb-8">
        {/* Onboarding step pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-50 text-violet-700 border border-violet-100 dark:bg-violet-500/10 dark:border-violet-500/20 text-xs font-semibold dark:text-violet-300 mb-4">
          <span className="w-5 h-5 rounded-full bg-violet-200 dark:bg-violet-500/30 flex items-center justify-center text-[10px] font-bold text-violet-700 dark:text-violet-300">2</span>
          Step 2 of 4 — Select your courses
        </div>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-1">
              My <span className="gradient-text">Courses</span>
            </h1>
            <p className="text-slate-500 dark:text-white/40 text-sm">
              <span className="text-violet-600 dark:text-violet-400 font-semibold">{data?.cursus_name}</span>
              {' · '}Semester <span className="text-slate-700 dark:text-white/60 font-semibold">{data?.semester_name}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-white/40">
              <svg className="w-4 h-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Auto-saved
            </div>
            {enrolled > 0 && (
              <button
                onClick={() => navigate('/availabilities')}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold transition-colors shadow-sm"
              >
                Next: Set Availabilities →
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-5 p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              {enrolled}/{total} courses qualified
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400">{enrolledEcts} / {totalEcts} ECTS in planning</span>
          </div>
          <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-500"
              style={{ width: total > 0 ? `${(enrolled / total) * 100}%` : '0%' }}
            />
          </div>
          {/* Quick stats */}
          <div className="flex gap-4 mt-3 flex-wrap">
            {retakeCount > 0 && (
              <span className="text-[11px] text-amber-700 dark:text-amber-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-amber-500 dark:bg-amber-400 rounded-full" />
                {retakeCount} retake{retakeCount > 1 ? 's' : ''} — high priority
              </span>
            )}
            {validatedCount > 0 && (
              <span className="text-[11px] text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 dark:bg-emerald-400 rounded-full" />
                {validatedCount} validated — excluded from schedule
              </span>
            )}
            {enrolled === 0 && (
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Select a status for each course to help the AI build your schedule
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Filter tabs ── */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {[
          { key: 'all', label: 'All courses', count: total },
          { key: 'pending', label: 'Not selected', count: total - enrolled },
          { key: 'in_progress', label: 'In Progress', count: data?.courses?.filter((c) => c.enrollment_status === 'in_progress').length ?? 0 },
          { key: 'retake', label: 'Retake', count: retakeCount },
          { key: 'validated', label: 'Validated', count: validatedCount },
        ].map(({ key, label, count }) => (
          <button
            key={key}
            id={`filter-${key}`}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border
              ${filter === key
                ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200 hover:border-slate-300 dark:bg-white/[0.03] dark:text-white/50 dark:border-white/8 dark:hover:border-white/15 dark:hover:text-white/70'
              }`}
          >
            {label}
            {count > 0 && (
              <span className={`ml-1.5 text-[10px] ${filter === key ? 'text-violet-200' : 'text-slate-400 dark:text-white/25'}`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Status legend ── */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {Object.entries(STATUS_CONFIG).map(([key, c]) => (
          <div key={key} className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-white/40">
            <span className={`w-2 h-2 rounded-full ${c.dot}`} />
            <span className="font-medium text-slate-700 dark:text-white/60">{c.label}</span>
            <span className="text-slate-400 dark:text-white/20">→ {c.aiHint}</span>
          </div>
        ))}
      </div>

      {/* ── Course groups (current semester) ── */}
      {filteredCourses.filter(c => !c.is_retake).length === 0 && !hasRetakeCourses ? (
        <div className="text-center py-16 text-slate-500 dark:text-slate-400">
          <div className="text-4xl mb-3">🎯</div>
          <p className="font-semibold text-slate-700 dark:text-slate-300">No courses match this filter</p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Current semester courses */}
          {Object.entries(groups).map(([key, group]) => (
            <TeachingUnitGroup
              key={key}
              tuName={group.tu?.name ?? 'Other Courses'}
              tuCode={group.tu?.code}
              tuEcts={group.tu?.ects_required}
              courses={group.courses}
              onStatusChange={handleStatusChange}
              savingId={savingId}
            />
          ))}

          {/* Retake semester sections (German Wiederholung) */}
          {hasRetakeCourses && (
            <>
              <div className="flex items-center gap-3 pt-4 pb-1">
                <div className="h-px flex-1 bg-amber-500/20" />
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20">
                  <span className="text-amber-400 text-xs">⚠</span>
                  <span className="text-xs font-semibold text-amber-300">Semestres en Rattrapage (Wiederholung)</span>
                </div>
                <div className="h-px flex-1 bg-amber-500/20" />
              </div>
              {Object.entries(retakeGroups)
                .sort((a, b) => a[1].semNumber - b[1].semNumber)
                .map(([semKey, { semNumber, tuGroups }]) => (
                  <div key={semKey} className="space-y-2">
                    <div className="flex items-center gap-2 px-1">
                      <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">S{semNumber} — Rattrapage</span>
                      <div className="h-px flex-1 bg-amber-500/10" />
                    </div>
                    {Object.entries(tuGroups).map(([tuKey, group]) => (
                      <div key={tuKey} className="border border-amber-500/20 rounded-2xl overflow-visible bg-amber-500/[0.02]">
                        <TeachingUnitGroup
                          tuName={group.tu?.name ?? 'Other Courses'}
                          tuCode={group.tu?.code}
                          tuEcts={group.tu?.ects_required}
                          courses={group.courses}
                          onStatusChange={handleStatusChange}
                          savingId={savingId}
                        />
                      </div>
                    ))}
                  </div>
                ))
              }
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SubjectsPage;
