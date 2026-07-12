import PropTypes from 'prop-types';
import Card from '../ui/Card';
import Tooltip from '../ui/Tooltip';

const BadgeDisplay = ({ badges = [] }) => {
  return (
    <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <span>🏆 Mes Badges de Réussite</span>
        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
          {badges.filter((b) => b.isEarned).length} / {badges.length}
        </span>
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
        {badges.map((badge) => (
          <Tooltip
            key={badge.id}
            content={badge.description}
            placement="top"
          >
            <div
              className={`flex flex-col items-center p-4 rounded-2xl border transition-all duration-300 select-none ${
                badge.isEarned
                  ? 'bg-slate-900/40 border-violet-500/20 shadow-glow-sm scale-100 hover:scale-105'
                  : 'bg-slate-950/20 border-white/5 opacity-50 grayscale hover:opacity-75'
              }`}
            >
              {/* Badge Icon */}
              <div
                className={`w-14 h-14 rounded-full flex items-center justify-center text-3xl mb-3 ${
                  badge.isEarned
                    ? 'bg-violet-500/10 border border-violet-500/30 animate-pulse'
                    : 'bg-white/5 border border-white/5'
                }`}
              >
                {badge.icon}
              </div>

              {/* Title */}
              <span className="text-xs font-bold text-white text-center truncate w-full">
                {badge.title}
              </span>

              {/* Status */}
              <span className={`text-[9px] uppercase font-bold mt-1.5 ${
                badge.isEarned ? 'text-emerald-400' : 'text-white/30'
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
