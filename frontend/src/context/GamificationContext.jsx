import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useAcademicData } from './AcademicDataContext';

const GamificationContext = createContext(null);

export const useGamification = () => {
  const context = useContext(GamificationContext);
  if (!context) {
    throw new Error('useGamification must be used within GamificationProvider');
  }
  return context;
};

export const GamificationProvider = ({ children }) => {
  const { subjects, ectsProgression } = useAcademicData();
  const [streak, setStreak] = useState(0);
  const [badges, setBadges] = useState([]);
  const [activeCelebration, setActiveCelebration] = useState(null);

  // Initialize streak and badges on mount
  useEffect(() => {
    // Retrieve or initialize streak from localStorage
    const savedStreak = parseInt(localStorage.getItem('study_streak') || '0', 10);
    const lastActiveDate = localStorage.getItem('last_active_date');
    const today = new Date().toDateString();

    if (lastActiveDate) {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayStr = yesterday.toDateString();

      if (lastActiveDate === today) {
        setStreak(savedStreak);
      } else if (lastActiveDate === yesterdayStr) {
        // Increment streak since user is active on consecutive days
        const newStreak = savedStreak + 1;
        setStreak(newStreak);
        localStorage.setItem('study_streak', newStreak.toString());
        localStorage.setItem('last_active_date', today);
      } else {
        // Reset streak if gap is larger than 1 day
        setStreak(1);
        localStorage.setItem('study_streak', '1');
        localStorage.setItem('last_active_date', today);
      }
    } else {
      setStreak(1);
      localStorage.setItem('study_streak', '1');
      localStorage.setItem('last_active_date', today);
    }
  }, []);

  // Compute badges dynamically based on academic state
  useEffect(() => {
    if (!subjects) return;

    const validatedCount = subjects.filter((s) => s.validation_status === 'validated').count || subjects.filter((s) => s.validation_status === 'validated').length;
    const ectsPercentage = ectsProgression?.percentage || 0;

    const initialBadges = [
      {
        id: 'first_subject',
        title: 'Premier Pas',
        description: 'Valider votre première matière',
        icon: '🎯',
        isEarned: validatedCount >= 1,
      },
      {
        id: 'ects_25',
        title: 'Quart de Route',
        description: 'Atteindre 25% des crédits ECTS visés',
        icon: '🥉',
        isEarned: ectsPercentage >= 25,
      },
      {
        id: 'ects_50',
        title: 'Mi-parcours',
        description: 'Atteindre 50% des crédits ECTS visés',
        icon: '🥈',
        isEarned: ectsPercentage >= 50,
      },
      {
        id: 'ects_75',
        title: 'Dernière Ligne Droite',
        description: 'Atteindre 75% des crédits ECTS visés',
        icon: '🥇',
        isEarned: ectsPercentage >= 75,
      },
      {
        id: 'ects_100',
        title: 'Diplômé !',
        description: 'Atteindre 100% des crédits ECTS visés',
        icon: '🎓',
        isEarned: ectsPercentage >= 100,
      },
      {
        id: 'streak_3',
        title: 'Régularité',
        description: 'Atteindre une série d\'études de 3 jours',
        icon: '🔥',
        isEarned: streak >= 3,
      },
    ];

    setBadges(initialBadges);

    // Check for new achievements to trigger celebrations
    const previouslyEarned = JSON.parse(localStorage.getItem('earned_badges') || '[]');
    const newlyEarned = initialBadges.filter(b => b.isEarned && !previouslyEarned.includes(b.id));

    if (newlyEarned.length > 0) {
      // Trigger celebration for the first new badge
      const newBadge = newlyEarned[0];
      setActiveCelebration({
        type: 'badge_earned',
        title: `Badge débloqué : ${newBadge.title}`,
        message: newBadge.description,
        icon: newBadge.icon,
      });

      // Save to localStorage
      const updatedEarned = [...previouslyEarned, ...newlyEarned.map(b => b.id)];
      localStorage.setItem('earned_badges', JSON.stringify(updatedEarned));
    }
  }, [subjects, ectsProgression, streak]);

  const triggerCelebration = (type, title, message, icon) => {
    setActiveCelebration({ type, title, message, icon });
  };

  const clearCelebration = () => {
    setActiveCelebration(null);
  };

  const value = {
    streak,
    badges,
    activeCelebration,
    triggerCelebration,
    clearCelebration,
  };

  return <GamificationContext.Provider value={value}>{children}</GamificationContext.Provider>;
};

GamificationProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
