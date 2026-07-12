import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import ConfettiAnimation from './ConfettiAnimation';

const CelebrationAnimation = ({ trigger, message, duration = 4000, onClose }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      if (onClose) onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!visible) return null;

  const triggerIcons = {
    subject_validated: '🎓',
    milestone_reached: '🏆',
    streak_achieved: '🔥',
    badge_earned: '🏅'
  };

  const icon = triggerIcons[trigger] || '🌟';

  return (
    <div className="fixed inset-0 z-[99] flex items-center justify-center bg-slate-950/85 backdrop-blur-md animate-fade-in">
      <ConfettiAnimation duration={duration} />

      <div className="text-center px-6 py-8 max-w-sm mx-auto glass-card border border-white/10 rounded-2xl glow-violet scale-95 animate-slide-up bg-slate-900/90 shadow-2xl relative overflow-hidden">
        {/* Neon decoration */}
        <div className="absolute -top-10 -left-10 w-24 h-24 bg-violet-600/30 rounded-full blur-2xl" />
        <div className="absolute -bottom-10 -right-10 w-24 h-24 bg-cyan-600/30 rounded-full blur-2xl" />

        {/* Large icon */}
        <div className="w-24 h-24 bg-violet-500/10 border border-violet-500/20 rounded-full flex items-center justify-center text-5xl mx-auto mb-6 animate-bounce">
          {icon}
        </div>

        {/* Text */}
        <h2 className="text-2xl font-black text-white mb-3 tracking-wide">
          {trigger === 'subject_validated' && 'Matière Validée !'}
          {trigger === 'milestone_reached' && 'Palier ECTS Rejoint !'}
          {trigger === 'streak_achieved' && 'Série d\'Études !'}
          {trigger === 'badge_earned' && 'Badge Déverrouillé !'}
          {!triggerIcons[trigger] && 'Félicitations !'}
        </h2>
        <p className="text-white/80 text-sm leading-relaxed mb-6 font-medium">
          {message || 'Excellent travail ! Continuez ainsi vers votre diplôme.'}
        </p>

        {/* Action Button */}
        <button
          onClick={() => {
            setVisible(false);
            if (onClose) onClose();
          }}
          className="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 text-white font-bold rounded-xl shadow-glow-sm hover:shadow-glow-violet hover:-translate-y-0.5 transition-all text-sm"
        >
          Super !
        </button>
      </div>
    </div>
  );
};

CelebrationAnimation.propTypes = {
  trigger: PropTypes.oneOf(['subject_validated', 'milestone_reached', 'streak_achieved', 'badge_earned']).isRequired,
  message: PropTypes.string,
  duration: PropTypes.number,
  onClose: PropTypes.func
};

export default CelebrationAnimation;
