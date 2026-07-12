import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

const ConfettiAnimation = ({ particleCount = 80, duration = 3000, colors = ['#8b5cf6', '#6366f1', '#22d3ee', '#34d399', '#f43f5e', '#fbbf24'] }) => {
  const [particles, setParticles] = useState([]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Generate particles
    const generated = Array.from({ length: particleCount }).map((_, index) => {
      const size = Math.random() * 8 + 6; // 6px to 14px
      const left = Math.random() * 100; // 0% to 100%
      const delay = Math.random() * 1.5; // delay up to 1.5s
      const speed = Math.random() * 2 + 2; // speed between 2s and 4s
      const rotationSpeed = Math.random() * 360 + 360; // deg
      const color = colors[Math.floor(Math.random() * colors.length)];
      
      return {
        id: index,
        size,
        left,
        delay,
        speed,
        rotationSpeed,
        color,
        shape: Math.random() > 0.5 ? 'circle' : 'rect',
      };
    });

    setParticles(generated);

    // Stop after duration
    const timer = setTimeout(() => {
      setVisible(false);
    }, duration);

    return () => clearTimeout(timer);
  }, [particleCount, duration, colors]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-[100] overflow-hidden">
      {/* Styles for falling animation */}
      <style>{`
        @keyframes confetti-fall {
          0% {
            transform: translateY(-20px) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(105vh) rotate(720deg);
            opacity: 0;
          }
        }
        .confetti-particle {
          position: absolute;
          top: -20px;
          animation-name: confetti-fall;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
        }
      `}</style>

      {particles.map((p) => (
        <div
          key={p.id}
          className="confetti-particle"
          style={{
            left: `${p.left}%`,
            width: `${p.size}px`,
            height: p.shape === 'circle' ? `${p.size}px` : `${p.size * 1.5}px`,
            borderRadius: p.shape === 'circle' ? '50%' : '2px',
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.speed}s`,
            transform: `rotate(${Math.random() * 360}deg)`,
          }}
        />
      ))}
    </div>
  );
};

ConfettiAnimation.propTypes = {
  particleCount: PropTypes.number,
  duration: PropTypes.number,
  colors: PropTypes.arrayOf(PropTypes.string),
};

export default ConfettiAnimation;
