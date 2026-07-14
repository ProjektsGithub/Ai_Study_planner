import PropTypes from 'prop-types';

const Card = ({ children, className = '', hover = true, gradient = false, padding = 'p-6', onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`
        relative rounded-2xl border border-slate-100 dark:border-white/10 backdrop-blur-md
        bg-white dark:bg-white/[0.05] shadow-card transition-all duration-300
        ${hover ? 'hover:shadow-md hover:-translate-y-1 hover:border-violet-500/20 dark:hover:border-violet-500/30' : ''}
        ${gradient ? 'bg-gradient-to-br from-violet-500/5 to-indigo-500/5 dark:from-violet-500/10 dark:to-indigo-500/5' : ''}
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
  onClick: PropTypes.func,
};

export default Card;
