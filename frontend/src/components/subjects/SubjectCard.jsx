import PropTypes from 'prop-types';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import RiskIndicator from './RiskIndicator';

const StarBar = ({ value, max = 5, color = 'violet' }) => {
  const colors = {
    violet: 'bg-violet-500',
    amber: 'bg-amber-500',
    cyan: 'bg-cyan-500',
  };
  return (
    <div className="flex gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-all ${i < value ? colors[color] : 'bg-white/10'}`}
        />
      ))}
    </div>
  );
};

StarBar.propTypes = {
  value: PropTypes.number.isRequired,
  max: PropTypes.number,
  color: PropTypes.string,
};

const SubjectCard = ({ subject, riskScore, onEdit, onDelete }) => {
  const statusColors = {
    in_progress: 'violet',
    validated: 'success',
    not_started: 'cyan',
    failed: 'error',
  };

  const statusLabels = {
    in_progress: 'In Progress',
    validated: 'Validated',
    not_started: 'Not Started',
    failed: 'Failed / Retake',
  };

  return (
    <Card className="relative overflow-hidden group flex flex-col justify-between h-full">
      {/* Top gradient bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-500 to-indigo-500 opacity-50" />

      <div>
        <div className="flex justify-between items-start gap-2 mb-4">
          <h3 className="text-base font-bold text-white group-hover:text-violet-300 transition-colors leading-snug truncate">
            {subject.name}
          </h3>
          <div className="flex gap-1 flex-shrink-0">
            <button
              onClick={() => onEdit(subject)}
              className="p-1.5 rounded-lg text-white/30 hover:text-violet-400 hover:bg-violet-500/10 transition-all"
              aria-label="Edit"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onDelete(subject.id)}
              className="p-1.5 rounded-lg text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all"
              aria-label="Delete"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-3.5 text-sm">
          <div>
            <div className="flex justify-between text-[11px] text-white/40 mb-1">
              <span>Study Priority</span>
              <span className="font-semibold text-white/60">{subject.priority}/5</span>
            </div>
            <StarBar value={subject.priority} color="violet" />
          </div>

          <div>
            <div className="flex justify-between text-[11px] text-white/40 mb-1">
              <span>Perceived Difficulty</span>
              <span className="font-semibold text-white/60">{subject.difficulty}/5</span>
            </div>
            <StarBar value={subject.difficulty} color="amber" />
          </div>

          {/* ECTS and Coeff Info */}
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/5 text-[11px]">
            <div className="flex flex-col">
              <span className="text-white/40">ECTS Credits</span>
              <span className="text-white font-bold mt-0.5">{subject.ects_credits ?? 'N/A'}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-white/40">Coefficient</span>
              <span className="text-white font-bold mt-0.5">{subject.coefficient ?? '1.0'}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3.5 border-t border-white/5 flex items-center justify-between">
        <Badge variant={statusColors[subject.validation_status] || 'info'}>
          {statusLabels[subject.validation_status] || subject.validation_status}
        </Badge>

        <RiskIndicator
          level={riskScore?.risk_level || 'low'}
          factors={riskScore?.factors || []}
        />
      </div>

      {subject.exam_date && (
        <div className="flex items-center gap-2 text-[10px] text-cyan-400/80 mt-2.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Exam: {new Date(subject.exam_date).toLocaleDateString('en-US')}
        </div>
      )}
    </Card>
  );
};

SubjectCard.propTypes = {
  subject: PropTypes.object.isRequired,
  riskScore: PropTypes.object,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default SubjectCard;
