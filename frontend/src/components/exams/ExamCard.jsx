import PropTypes from 'prop-types';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const ExamCard = ({ exam, onEdit, onDelete }) => {
  const daysUntil = exam.days_until ?? 0;
  const isUrgent = daysUntil <= 2;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };

  return (
    <Card
      className={`
        relative overflow-hidden group flex flex-col justify-between h-full
        ${isUrgent ? 'border-red-500/20 bg-red-500/[0.02]' : ''}
      `}
    >
      {/* Top indicator bar */}
      <div
        className={`
          absolute top-0 left-0 right-0 h-0.5 opacity-55
          ${isUrgent ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-indigo-500'}
        `}
      />

      <div>
        <div className="flex justify-between items-start gap-2 mb-3.5">
          <h3 className="text-base font-bold text-white group-hover:text-blue-300 transition-colors leading-snug truncate">
            {exam.course_name}
          </h3>
          <div className="flex gap-1 flex-shrink-0">
            <button
              onClick={() => onEdit(exam)}
              className="p-1.5 rounded-lg text-white/30 hover:text-blue-400 hover:bg-blue-500/10 transition-all"
              aria-label="Edit"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onDelete(exam.id)}
              className="p-1.5 rounded-lg text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all"
              aria-label="Delete"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-2.5 text-xs text-white/60">
          {/* Date and Time */}
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="capitalize">{formatDate(exam.exam_date)}</span>
          </div>

          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{exam.exam_time ? exam.exam_time.slice(0, 5) : '08:00'} (Duration: {exam.duration_minutes ?? 120} min)</span>
          </div>

          {/* Location */}
          {exam.location && (
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="truncate">{exam.location}</span>
            </div>
          )}

          {/* Prep recommendation */}
          <div className="flex items-center gap-2 text-violet-400 font-medium pt-2 border-t border-white/5">
            <svg className="w-4 h-4 text-violet-400/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13" />
            </svg>
            <span>Suggested study volume: {exam.weight ? Math.round(exam.weight * 50) : 30}h</span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
        <Badge variant={isUrgent ? 'error' : 'info'} className={isUrgent ? 'animate-pulse' : ''}>
          {daysUntil === 0 ? "Today" : daysUntil === 1 ? "Tomorrow" : `${daysUntil} days left`}
        </Badge>
        {exam.exam_type && (
          <span className="text-[10px] text-white/30 font-semibold uppercase tracking-wider">
            {exam.exam_type}
          </span>
        )}
      </div>
    </Card>
  );
};

ExamCard.propTypes = {
  exam: PropTypes.object.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default ExamCard;
