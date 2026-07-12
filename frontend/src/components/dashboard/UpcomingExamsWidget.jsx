import { useNavigate } from 'react-router-dom';
import { useAcademicData } from '../../context/AcademicDataContext';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const UpcomingExamsWidget = () => {
  const navigate = useNavigate();
  const { upcomingExams, loading } = useAcademicData();

  if (loading && upcomingExams.length === 0) {
    return (
      <Card className="h-full animate-pulse bg-white/5 border border-white/10 p-5 rounded-2xl">
        <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-8 bg-white/10 rounded w-full" />
          <div className="h-8 bg-white/10 rounded w-full" />
        </div>
      </Card>
    );
  }

  // Slice next 3 exams
  const nextExams = upcomingExams.slice(0, 3);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'short',
    });
  };

  return (
    <Card
      onClick={() => navigate('/exams')}
      className="cursor-pointer hover:border-violet-500/40 relative overflow-hidden group flex flex-col justify-between"
    >
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-cyan-500 opacity-60" />

      <div>
        <div className="flex justify-between items-center mb-4">
          <span className="text-xs text-white/40 font-semibold uppercase tracking-wider">Upcoming Exams</span>
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        {nextExams.length > 0 ? (
          <div className="space-y-2.5">
            {nextExams.map((exam) => {
              const daysUntil = exam.days_until ?? 0;
              const isUrgent = daysUntil <= 2;
              return (
                <div
                  key={exam.id}
                  className={`
                    flex items-center justify-between p-2.5 rounded-xl border transition-colors
                    ${isUrgent
                      ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10'
                      : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04]'}
                  `}
                >
                  <div className="flex flex-col min-w-0 pr-2">
                    <span className="text-sm font-semibold text-white truncate">{exam.course_name}</span>
                    <span className="text-[10px] text-white/40 mt-0.5">
                      {formatDate(exam.exam_date)} · {exam.exam_time ? exam.exam_time.slice(0, 5) : '08:00'}
                    </span>
                  </div>
                  <Badge variant={isUrgent ? 'error' : 'info'} className={isUrgent ? 'animate-pulse' : ''}>
                    {daysUntil === 0 ? "Today" : daysUntil === 1 ? 'Tomorrow' : `${daysUntil} days left`}
                  </Badge>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-5">
            <p className="text-sm font-medium text-white/50">No exams scheduled</p>
            <p className="text-xs text-white/30 mt-1">Plan your revisions.</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default UpcomingExamsWidget;
