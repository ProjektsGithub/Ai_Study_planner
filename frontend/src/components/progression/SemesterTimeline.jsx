import PropTypes from 'prop-types';

const SemesterTimeline = ({ selectedSemester, onSemesterSelect, currentSemester = 1 }) => {
  const semesters = [1, 2, 3, 4, 5, 6];

  return (
    <div className="w-full py-6 overflow-x-auto select-none">
      <div className="flex justify-between items-center min-w-[500px] relative px-4">
        {/* Horizontal bar */}
        <div className="absolute top-[34px] left-8 right-8 h-1 bg-white/10 rounded-full" />

        {semesters.map((s) => {
          const isSelected = selectedSemester === `S${s}`;
          const isCurrent = currentSemester === s;
          const label = `Semester ${s}`;
          const name = `S${s}`;

          return (
            <button
              key={s}
              type="button"
              onClick={() => onSemesterSelect(name)}
              className="flex flex-col items-center relative z-10 focus:outline-none group"
            >
              {/* Semester number node */}
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all duration-300
                  ${isSelected
                    ? 'bg-violet-600 border-violet-400 text-white shadow-glow-sm'
                    : isCurrent
                      ? 'bg-violet-500/20 border-violet-500/60 text-violet-300'
                      : 'bg-slate-900 border-white/10 text-white/50 group-hover:border-white/30 group-hover:text-white/80'}
                `}
              >
                {s}
              </div>
              <span
                className={`
                  text-[11px] mt-2 font-medium tracking-tight transition-colors
                  ${isSelected ? 'text-violet-300 font-bold' : isCurrent ? 'text-violet-400' : 'text-white/40'}
                `}
              >
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

SemesterTimeline.propTypes = {
  selectedSemester: PropTypes.string.isRequired,
  onSemesterSelect: PropTypes.func.isRequired,
  currentSemester: PropTypes.number,
};

export default SemesterTimeline;
