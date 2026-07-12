import { useNavigate } from 'react-router-dom';
import { useAcademicData } from '../../context/AcademicDataContext';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const RiskSubjectsWidget = () => {
  const navigate = useNavigate();
  const { riskScores, loading } = useAcademicData();

  if (loading && riskScores.length === 0) {
    return (
      <Card className="h-full animate-pulse bg-white/5 border border-white/10 p-5 rounded-2xl">
        <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-8 bg-white/10 rounded w-full" />
          <div className="h-8 bg-white/10 rounded w-full" />
        </div>
      </Card>
    );
  }

  // Filter high and medium risk subjects
  const atRisk = riskScores
    .filter((score) => score.risk_level === 'high' || score.risk_level === 'medium')
    .slice(0, 3);

  const getRiskVariant = (level) => {
    if (level === 'high') return 'error';
    if (level === 'medium') return 'warning';
    return 'success';
  };

  const getRiskLabel = (level) => {
    if (level === 'high') return 'High Risk';
    if (level === 'medium') return 'Medium Risk';
    return 'Low Risk';
  };

  return (
    <Card
      onClick={() => navigate('/subjects')}
      className="cursor-pointer hover:border-violet-500/40 relative overflow-hidden group flex flex-col justify-between"
    >
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-amber-500 to-red-500 opacity-60" />

      <div>
        <div className="flex justify-between items-center mb-4">
          <span className="text-xs text-white/40 font-semibold uppercase tracking-wider">At-Risk Subjects</span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>

        {atRisk.length > 0 ? (
          <div className="space-y-2.5">
            {atRisk.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/5"
              >
                <div className="flex flex-col min-w-0 pr-2">
                   <span className="text-sm font-semibold text-white/90 truncate">{item.course_name}</span>
                   <span className="text-[10px] text-white/40 truncate">
                    {item.factors && item.factors.length > 0 ? item.factors[0] : 'Academic support needed'}
                   </span>
                </div>
                <Badge variant={getRiskVariant(item.risk_level)}>
                  {getRiskLabel(item.risk_level)}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-5">
            <p className="text-sm font-medium text-emerald-400">All subjects are validated or stable!</p>
            <p className="text-xs text-white/30 mt-1">Excellent academic performance.</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default RiskSubjectsWidget;
