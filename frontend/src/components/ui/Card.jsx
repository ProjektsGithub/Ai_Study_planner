import PropTypes from 'prop-types';

const Card = ({ children, className = '', hover = true, gradient = false, padding = 'p-6' }) => {
  return (
    <div
      className={`
        relative rounded-2xl border border-white/10 backdrop-blur-md
        bg-white/[0.05] shadow-card transition-all duration-300
        ${hover ? 'hover:bg-white/[0.08] hover:border-violet-500/30 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgba(0,0,0,0.4),0_0_15px_rgba(139,92,246,0.1)]' : ''}
        ${gradient ? 'bg-gradient-to-br from-violet-500/10 to-indigo-500/5' : ''}
        ${padding}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  hover: PropTypes.bool,
  gradient: PropTypes.bool,
  padding: PropTypes.string,
};

export default Card;
