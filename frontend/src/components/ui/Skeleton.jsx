import PropTypes from 'prop-types';

const Skeleton = ({ variant = 'rectangle', width = '100%', height = '1rem', className = '' }) => {
  const isCircle = variant === 'circle';
  const style = {
    width,
    height: isCircle ? width : height,
  };

  return (
    <div
      className={`bg-white/5 rounded-xl animate-pulse ${isCircle ? 'rounded-full' : ''} ${className}`}
      style={style}
    />
  );
};

Skeleton.propTypes = {
  variant: PropTypes.oneOf(['circle', 'rectangle']),
  width: PropTypes.string,
  height: PropTypes.string,
  className: PropTypes.string,
};

export default Skeleton;
