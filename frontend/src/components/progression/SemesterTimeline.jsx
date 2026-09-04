import PropTypes from 'prop-types';
import { useLanguage } from '../../context/LanguageContext';

const SemesterTimeline = ({ selectedSemester, onSemesterSelect, currentSemester = 1 }) => {
  const { t } = useLanguage();
  const maxSem = Math.max(6, currentSemester || 1);
  const semesters = Array.from({ length: maxSem }, (_, i) => i + 1);

  return (
    <div className="w-full py-6 overflow-x-auto select-none">
      <div className="flex justify-between items-center min-w-[500px] relative px-4">
        {/* Horizontal bar */}
        <div className="absolute top-[34px] left-8 right-8 h-1 bg-slate-200 dark:bg-white/10 rounded-full" />

        {semesters.map((s) => {
          const isSelected = selectedSemester === `S${s}`;
          const isCurrent = currentSemester === s;
          const label = t('progression.semester_label', { s });
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
                      ? 'bg-violet-500/20 border-violet-500/60 text-violet-700 dark:text-violet-300'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-white/10 text-slate-500 dark:text-white/50 group-hover:border-violet-300 group-hover:text-slate-800 dark:group-hover:text-white/80'}
                `}
              >
                {s}
              </div>
              <span
                className={`
                  text-[11px] mt-2 font-medium tracking-tight transition-colors
                  ${isSelected ? 'text-violet-600 dark:text-violet-300 font-bold' : isCurrent ? 'text-violet-500 dark:text-violet-400 font-semibold' : 'text-slate-400 dark:text-white/40'}
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
