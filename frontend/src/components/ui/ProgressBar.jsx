import PropTypes from 'prop-types';

const ProgressBar = ({ value, max = 100, showLabel = true, className = '', label = '' }) => {
  const percentage = max > 0 ? Math.min(Math.round((value / max) * 100), 100) : 0;

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1.5 text-xs text-white/50">
          <span>{label}</span>
          <span className="font-semibold text-white/80">{percentage}%</span>
        </div>
      )}
      <div className="w-full h-2.5 bg-white/5 rounded-full overflow-hidden border border-white/5 relative">
        <div
          className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-1000 ease-out relative progress-animated"
          style={{ width: `${percentage}%`, '--progress-value': `${percentage}%` }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.15)_50%,transparent_100%)] bg-[length:200%_100%] animate-[shimmer_2s_infinite]" />
        </div>
      </div>
    </div>
  );
};

ProgressBar.propTypes = {
  value: PropTypes.number.isRequired,
  max: PropTypes.number,
  showLabel: PropTypes.bool,
  className: PropTypes.string,
  label: PropTypes.string,
};

export default ProgressBar;
