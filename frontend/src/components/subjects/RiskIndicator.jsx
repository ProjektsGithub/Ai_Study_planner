import PropTypes from 'prop-types';
import Badge from '../ui/Badge';
import Tooltip from '../ui/Tooltip';

const RiskIndicator = ({ level = 'low', factors = [], showTooltip = true }) => {
  const getVariant = () => {
    if (level === 'high') return 'error';
    if (level === 'medium') return 'warning';
    return 'success';
  };

  const getLabel = () => {
    if (level === 'high') return 'Risque Élevé';
    if (level === 'medium') return 'Risque Moyen';
    return 'Risque Faible';
  };

  const getIcon = () => {
    if (level === 'high') {
      return (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    if (level === 'medium') {
      return (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    return (
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
      </svg>
    );
  };

  const badgeContent = (
    <Badge variant={getVariant()} icon={getIcon()}>
      {getLabel()}
    </Badge>
  );

  if (showTooltip && factors && factors.length > 0) {
    const tooltipContent = (
      <div className="space-y-1">
        <p className="font-bold text-white mb-1">Facteurs de risque :</p>
        <ul className="list-disc list-inside space-y-0.5">
          {factors.map((f, idx) => (
            <li key={idx} className="text-[10px]">{f}</li>
          ))}
        </ul>
      </div>
    );
    return <Tooltip content={tooltipContent}>{badgeContent}</Tooltip>;
  }

  return badgeContent;
};

RiskIndicator.propTypes = {
  level: PropTypes.oneOf(['low', 'medium', 'high']),
  factors: PropTypes.arrayOf(PropTypes.string),
  showTooltip: PropTypes.bool,
};

export default RiskIndicator;
