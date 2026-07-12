import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAcademicData } from '../context/AcademicDataContext';
import { useStudyPlan } from '../context/StudyPlanContext';
import { useGamification } from '../context/GamificationContext';
import apiClient from '../api/client';

// Widgets
import ECTSProgressWidget from '../components/dashboard/ECTSProgressWidget';
import RiskSubjectsWidget from '../components/dashboard/RiskSubjectsWidget';
import UpcomingExamsWidget from '../components/dashboard/UpcomingExamsWidget';
import WeekPlanWidget from '../components/dashboard/WeekPlanWidget';
import SetupProgressBanner from '../components/dashboard/SetupProgressBanner';

// Gamification
import StreakCounter from '../components/gamification/StreakCounter';
import BadgeDisplay from '../components/gamification/BadgeDisplay';

// UI Components
import Card from '../components/ui/Card';
import Skeleton from '../components/ui/Skeleton';

// ─── Quick Actions config ─────────────────────────────────────────────────────
const QUICK_ACTIONS = [
  {
    id: 'my-courses',
    label: 'My Courses',
    description: 'Select & qualify your semester courses',
    href: '/subjects',
    gradient: 'from-violet-600 to-indigo-500',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    id: 'exam-schedule',
    label: 'Exam Schedule',
    description: 'Plan your key evaluation dates',
    href: '/exams',
    gradient: 'from-blue-600 to-cyan-500',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    id: 'ai-recommendations',
    label: 'AI Recommendations',
    description: 'Performance analysis and study priorities',
    href: '/recommendations',
    gradient: 'from-amber-600 to-red-500',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
];

// ─── Main Component ───────────────────────────────────────────────────────────
const DashboardPage = () => {
  const { academicProfile, loading: academicLoading, fetchAllData } = useAcademicData();
  const { currentPlan, loading: planLoading, fetchCurrentPlan } = useStudyPlan();
  const { streak, badges } = useGamification();

  const [setupStatus, setSetupStatus] = useState(null);
  const [setupLoading, setSetupLoading] = useState(true);

  const fetchSetupStatus = useCallback(async () => {
    setSetupLoading(true);
    try {
      const res = await apiClient.get('/api/v1/setup/status');
      setSetupStatus(res.data);
    } catch {
      // Non-critical — don't block the dashboard
      setSetupStatus(null);
    } finally {
      setSetupLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    fetchCurrentPlan();
    fetchSetupStatus();
  }, [fetchAllData, fetchCurrentPlan, fetchSetupStatus]);

  const loading = academicLoading || planLoading;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">

      {/* ── Header with Streak Counter ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1.5">
            Hello{academicProfile?.cursus_name ? `, ${academicProfile.cursus_name}` : ''}!
          </h1>
          <p className="text-white/40 text-sm">
            Here is the progress of your academic success.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-violet-500/10 border border-violet-500/20 px-4 py-2.5 rounded-2xl shadow-glow-sm">
          <span className="text-2xl animate-bounce">🔥</span>
          <div>
            <p className="text-xs text-white/50 font-medium leading-none">Study Streak</p>
            <p className="text-base font-bold text-white mt-1">{streak} day{streak > 1 ? 's' : ''}</p>
          </div>
        </div>
      </div>

      {/* ── Onboarding Setup Banner ── */}
      {!setupLoading && setupStatus && !setupStatus.is_complete && (
        <SetupProgressBanner
          hasProfile={setupStatus.has_profile}
          hasCourses={setupStatus.has_courses}
          hasAvailabilities={setupStatus.has_availabilities}
          hasPlan={setupStatus.has_plan}
        />
      )}

      {/* ── Main Widgets Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 stagger-children">
        <ECTSProgressWidget />
        <RiskSubjectsWidget />
        <UpcomingExamsWidget />
        <WeekPlanWidget />
      </div>

      {/* ── Secondary Grid (Plan Summary + Gamification) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Weekly plan quick look */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-lg font-bold text-white">Your Weekly Plan</h2>
              <Link to="/planner" className="text-xs text-violet-400 hover:text-violet-300 font-semibold transition-colors">
                Manage Study Plan →
              </Link>
            </div>

            {loading ? (
              <div className="space-y-3">
                <Skeleton height="2rem" />
                <Skeleton height="2rem" />
                <Skeleton height="2rem" />
              </div>
            ) : currentPlan ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm text-white/60">
                  <span>Status: <span className="text-emerald-400 font-bold">Active</span></span>
                  <span>{currentPlan.sessions?.length || 0} sessions scheduled</span>
                </div>
                <div className="divider my-2" />
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5">
                    <p className="text-2xl font-bold text-white">{currentPlan.total_hours}h</p>
                    <p className="text-xs text-white/40 mt-1">Total Study Hours</p>
                  </div>
                  <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5">
                    <p className="text-2xl font-bold text-white">
                      {currentPlan.sessions?.filter((s) => s.completed)?.length || 0}
                    </p>
                    <p className="text-xs text-white/40 mt-1">Completed Sessions</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-white/50 mb-4">
                  {setupStatus?.has_courses
                    ? 'You have not generated a study plan for this week yet.'
                    : 'Complete your setup above to generate your first AI study plan.'}
                </p>
                {setupStatus?.has_courses && setupStatus?.has_availabilities ? (
                  <Link
                    to="/planner"
                    className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 text-white text-sm font-semibold shadow-glow-sm hover:shadow-glow-violet transition-all"
                  >
                    Generate My AI Plan
                  </Link>
                ) : (
                  <Link
                    to={setupStatus?.has_courses ? '/availabilities' : '/subjects'}
                    className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm font-semibold hover:bg-white/10 transition-all"
                  >
                    {setupStatus?.has_courses ? 'Set My Availabilities' : 'Select My Courses'} →
                  </Link>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Gamification column */}
        <div className="flex flex-col gap-6">
          <StreakCounter streak={streak} />
          <BadgeDisplay badges={badges} />
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4">Quick Shortcuts</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.id}
              id={`quick-action-${action.id}`}
              to={action.href}
              className="flex items-center gap-4 p-5 rounded-2xl border border-white/10 bg-white/[0.04] hover:bg-white/[0.07] hover:border-violet-500/30 transition-all duration-300 hover:-translate-y-1"
            >
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center text-white flex-shrink-0 shadow-glow-sm`}>
                {action.icon}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{action.label}</p>
                <p className="text-xs text-white/40 mt-0.5">{action.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
