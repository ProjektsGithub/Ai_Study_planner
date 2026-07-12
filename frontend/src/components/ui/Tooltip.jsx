import { useState } from 'react';
import PropTypes from 'prop-types';

const Tooltip = ({ content, children, placement = 'top', className = '' }) => {
  const [visible, setVisible] = useState(false);

  const placementClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && content && (
        <div
          className={`
            absolute z-50 px-3 py-2 text-xs text-white/90
            glass-strong rounded-xl shadow-card border border-white/10
            min-w-[150px] max-w-[250px] pointer-events-none animate-fade-in
            ${placementClasses[placement]}
          `}
        >
          {content}
        </div>
      )}
    </div>
  );
};

Tooltip.propTypes = {
  content: PropTypes.node,
  children: PropTypes.node.isRequired,
  placement: PropTypes.oneOf(['top', 'bottom', 'left', 'right']),
  className: PropTypes.string,
};

export default Tooltip;
