import PropTypes from 'prop-types';
import Card from '../ui/Card';
import Tooltip from '../ui/Tooltip';

const BadgeDisplay = ({ badges = [] }) => {
  return (
    <Card className="p-6 border border-slate-100 dark:border-white/10 bg-white shadow-sm">
      <h3 className="text-lg font-bold text-slate-850 dark:text-white mb-6 flex items-center justify-between gap-2">
        <span>🏆 Mes Badges</span>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-violet-50 text-violet-755 border border-violet-200 dark:bg-violet-500/20 dark:text-violet-300 dark:border-violet-500/30">
          {badges.filter((b) => b.isEarned).length} / {badges.length}
        </span>
      </h3>

      <div className="grid grid-cols-3 gap-3">
        {badges.map((badge) => (
          <Tooltip
            key={badge.id}
            content={badge.description}
            placement="top"
          >
            <div
              className={`flex flex-col items-center p-3 rounded-2xl border transition-all duration-300 select-none ${
                badge.isEarned
                  ? 'bg-slate-50 border-slate-150 shadow-sm scale-100 hover:scale-105 dark:bg-slate-900/40 dark:border-violet-500/20'
                  : 'bg-slate-100/50 border-slate-100/50 opacity-40 grayscale hover:opacity-60 dark:bg-slate-950/20 dark:border-white/5'
              }`}
            >
              {/* Badge Icon */}
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl mb-2.5 ${
                  badge.isEarned
                    ? 'bg-violet-50 border border-violet-100 dark:bg-violet-500/10 dark:border-violet-500/30'
                    : 'bg-slate-100 border border-slate-100 dark:bg-white/5 dark:border-white/5'
                }`}
              >
                {badge.icon}
              </div>

              {/* Title */}
              <span className="text-[10px] font-bold text-slate-700 dark:text-white text-center truncate w-full">
                {badge.title}
              </span>

              {/* Status */}
              <span className={`text-[9px] uppercase font-black mt-1 ${
                badge.isEarned ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-white/30'
              }`}>
                {badge.isEarned ? 'Débloqué' : 'Verrouillé'}
              </span>
            </div>
          </Tooltip>
        ))}
      </div>
    </Card>
  );
};

BadgeDisplay.propTypes = {
  badges: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
      isEarned: PropTypes.bool.isRequired,
    })
  ).isRequired,
};

export default BadgeDisplay;
