import PropTypes from 'prop-types';
import ConfettiAnimation from './ConfettiAnimation';

const MilestoneCelebration = ({ milestoneTitle, percentage, milestoneMessage, onClose }) => {
  return (
    <div className="fixed inset-0 z-[99] flex items-center justify-center bg-slate-950/85 backdrop-blur-md animate-fade-in">
      <ConfettiAnimation duration={5000} />

      <div className="text-center px-8 py-10 max-w-sm mx-auto glass-card border border-white/10 rounded-3xl glow-violet scale-95 animate-slide-up bg-slate-900/90 shadow-2xl relative overflow-hidden">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Circular Progress Ring */}
        <div className="relative w-36 h-36 mx-auto mb-6 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90">
            <circle
              cx="72"
              cy="72"
              r="60"
              className="stroke-white/5"
              strokeWidth="8"
              fill="transparent"
            />
            <circle
              cx="72"
              cy="72"
              r="60"
              className="stroke-violet-500"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray={2 * Math.PI * 60}
              strokeDashoffset={2 * Math.PI * 60 * (1 - percentage / 100)}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1.5s ease-out' }}
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-3xl font-black text-white">{percentage.toFixed(0)}%</span>
            <span className="text-[10px] text-white/40 uppercase font-bold tracking-wider">ECTS</span>
          </div>
        </div>

        {/* Header & Description */}
        <span className="text-xs uppercase font-extrabold tracking-widest text-violet-400 bg-violet-500/10 border border-violet-500/20 px-3 py-1 rounded-full">
          Palier Atteint
        </span>
        <h2 className="text-2xl font-black text-white mt-4 mb-2">{milestoneTitle || 'Nouveau Cap ECTS'}</h2>
        <p className="text-white/60 text-sm leading-relaxed mb-8">
          {milestoneMessage || `Félicitations, vous avez validé plus de ${percentage}% de vos crédits d'études nécessaires.`}
        </p>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="w-full py-3.5 bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 text-white font-bold rounded-2xl shadow-glow-sm hover:shadow-glow-violet hover:-translate-y-0.5 transition-all text-sm"
        >
          Continuer l'aventure
        </button>
      </div>
    </div>
  );
};

MilestoneCelebration.propTypes = {
  milestoneTitle: PropTypes.string,
  percentage: PropTypes.number.isRequired,
  milestoneMessage: PropTypes.string,
  onClose: PropTypes.func.isRequired,
};

export default MilestoneCelebration;
