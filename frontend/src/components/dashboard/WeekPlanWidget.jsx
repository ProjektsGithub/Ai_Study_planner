import { useNavigate } from 'react-router-dom';
import { useStudyPlan } from '../../context/StudyPlanContext';
import Card from '../ui/Card';

const WeekPlanWidget = () => {
  const navigate = useNavigate();
  const { currentPlan, loading } = useStudyPlan();

  if (loading && !currentPlan) {
    return (
      <Card className="h-full animate-pulse bg-slate-50/50 dark:bg-white/5 border border-slate-100 dark:border-white/10 p-5 rounded-2xl">
        <div className="h-4 bg-slate-200 dark:bg-white/10 rounded w-1/3 mb-4" />
        <div className="h-8 bg-slate-200 dark:bg-white/10 rounded w-1/2 mb-6" />
        <div className="h-10 bg-slate-200 dark:bg-white/10 rounded w-full" />
      </Card>
    );
  }

  const sessions = currentPlan?.sessions || [];
  const hours = currentPlan?.total_hours || 0;
  const count = currentPlan?.session_count || 0;

  return (
    <Card
      onClick={() => navigate('/planner')}
      className="cursor-pointer hover:border-violet-500/40 relative overflow-hidden group flex flex-col justify-between"
    >
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 opacity-60" />

      <div>
        <div className="flex justify-between items-center mb-3">
          <span className="text-xs text-slate-400 dark:text-white/40 font-semibold uppercase tracking-wider">Current Study Plan</span>
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400 flex items-center justify-center">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
        </div>

        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-3xl font-bold text-slate-800 dark:text-white leading-none">{hours}h</span>
          <span className="text-xs text-slate-400 dark:text-white/30 font-medium">of study split across {count} sessions</span>
        </div>
      </div>

      <div className="flex gap-1.5 justify-between">
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => {
          const dayMap = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday' };
          const hasSessions = sessions.some((s) => s.day === dayMap[day]);
          return (
            <div
              key={day}
              className={`
                flex flex-col items-center flex-1 py-2 rounded-lg border transition-all
                ${hasSessions
                  ? 'bg-emerald-50 border-emerald-100 text-emerald-700 font-semibold dark:bg-emerald-500/15 dark:border-emerald-500/30 dark:text-emerald-300'
                  : 'bg-slate-50 border-slate-100/50 text-slate-400 dark:bg-white/[0.01] dark:border-white/5 dark:text-white/30'}
              `}
            >
              <span className="text-[10px]">{day}</span>
              <span className={`w-1.5 h-1.5 rounded-full mt-1.5 ${hasSessions ? 'bg-emerald-500' : 'bg-transparent'}`} />
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default WeekPlanWidget;
