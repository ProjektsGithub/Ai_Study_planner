import PropTypes from 'prop-types';

const SubjectValidationStatus = ({ subject }) => {
  const status = subject.validation_status || 'in_progress';
  const grade = subject.grade;

  const renderIcon = () => {
    if (status === 'validated') {
      return (
        <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
          </svg>
        </div>
      );
    }
    if (status === 'failed') {
      return (
        <div className="w-8 h-8 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    }
    // In Progress
    return (
      <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center flex-shrink-0 relative">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      </div>
    );
  };

  return (
    <div className="flex items-center gap-3.5 p-3 rounded-xl bg-white/[0.02] border border-white/5">
      {renderIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white/90 truncate">{subject.name}</p>
        <p className="text-xs text-white/40 mt-0.5">
          {subject.ects_credits ?? 0} ECTS · Coeff {subject.coefficient ?? '1.0'}
        </p>
      </div>
      <div className="text-right">
        {grade !== undefined && grade !== null ? (
          <p className="text-sm font-bold text-white">{grade.toFixed(2)} / 20</p>
        ) : (
          <p className="text-xs font-semibold text-white/30">N/A</p>
        )}
        <p className="text-[10px] text-white/30 capitalize mt-0.5">
          {status === 'validated' ? 'Validated' : status === 'failed' ? 'Failed' : 'In progress'}
        </p>
      </div>
    </div>
  );
};

SubjectValidationStatus.propTypes = {
  subject: PropTypes.object.isRequired,
};

export default SubjectValidationStatus;
