import PropTypes from 'prop-types';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none select-none relative overflow-hidden';

  const variantClasses = {
    primary:
      'bg-gradient-to-r from-violet-600 to-indigo-500 text-white shadow-glow-sm hover:shadow-glow-violet hover:-translate-y-0.5 focus:ring-violet-500 after:absolute after:inset-0 after:bg-white/10 after:opacity-0 hover:after:opacity-100 after:transition-opacity',
    secondary:
      'bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-white/[0.05] dark:text-white/80 dark:hover:text-white dark:hover:bg-white/10 dark:border-white/10 border border-transparent focus:ring-violet-500',
    danger:
      'bg-gradient-to-r from-red-600 to-red-500 text-white hover:shadow-sm hover:-translate-y-0.5 focus:ring-red-500',
    success:
      'bg-gradient-to-r from-emerald-600 to-green-500 text-white hover:shadow-sm hover:-translate-y-0.5 focus:ring-green-500',
    outline:
      'border border-violet-200 dark:border-violet-500/50 text-violet-700 dark:text-violet-300 hover:bg-violet-50 dark:hover:bg-violet-500/10 hover:border-violet-300 focus:ring-violet-500',
    ghost:
      'text-slate-600 dark:text-white/60 hover:text-slate-950 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/8 focus:ring-violet-500',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-5 py-2.5 text-sm gap-2',
    lg: 'px-7 py-3.5 text-base gap-2.5',
  };

  const classes = `${baseClasses} ${variantClasses[variant] || variantClasses.primary} ${sizeClasses[size]} ${className}`;

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      <span className="relative z-10">{children}</span>
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'success', 'outline', 'ghost']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  onClick: PropTypes.func,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  className: PropTypes.string,
};

export default Button;
