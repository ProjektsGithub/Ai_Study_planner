import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

const StreakCounter = ({ streak = 0 }) => {
  const [longestStreak, setLongestStreak] = useState(0);

  useEffect(() => {
    const savedLongest = parseInt(localStorage.getItem('longest_streak') || '0', 10);
    if (streak > savedLongest) {
      setLongestStreak(streak);
      localStorage.setItem('longest_streak', streak.toString());
    } else {
      setLongestStreak(savedLongest);
    }
  }, [streak]);

  // Calculate progress towards next milestone (multiple of 7 days)
  const currentPace = streak % 7;
  const progressToNext = currentPace === 0 && streak > 0 ? 7 : currentPace;
  const nextMilestone = Math.ceil((streak || 1) / 7) * 7;

  return (
    <Card className="p-5 border border-white/10 bg-gradient-to-br from-violet-600/10 to-violet-900/5 backdrop-blur-md relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 right-0 -translate-y-1/2 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />

      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-xs uppercase font-extrabold text-white/40 tracking-wider">Série d'Études</h4>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-4xl font-black text-white">{streak}</span>
            <span className="text-sm font-semibold text-white/50">jours d'affilée</span>
          </div>
        </div>
        <span className="text-4xl animate-bounce">🔥</span>
      </div>

      {/* Progress to next 7-day milestone */}
      <div className="space-y-2">
        <div className="flex justify-between text-[11px] font-semibold text-white/50">
          <span>Prochain palier : {nextMilestone} jours</span>
          <span>{progressToNext}/7 jours</span>
        </div>
        <ProgressBar value={progressToNext} max={7} />
      </div>

      <div className="flex justify-between items-center border-t border-white/5 mt-4 pt-3 text-[11px] text-white/40">
        <span>🏆 Record personnel</span>
        <span className="font-bold text-amber-400">{longestStreak} jours</span>
      </div>
    </Card>
  );
};

StreakCounter.propTypes = {
  streak: PropTypes.number.isRequired,
};

export default StreakCounter;
