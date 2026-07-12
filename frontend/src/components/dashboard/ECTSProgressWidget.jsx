import { useNavigate } from 'react-router-dom';
import { useAcademicData } from '../../context/AcademicDataContext';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

const ECTSProgressWidget = () => {
  const navigate = useNavigate();
  const { ectsProgression, loading } = useAcademicData();

  if (loading && !ectsProgression) {
    return (
      <Card className="h-full animate-pulse bg-white/5 border border-white/10 p-5 rounded-2xl">
        <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
        <div className="h-8 bg-white/10 rounded w-1/2 mb-6" />
        <div className="h-3 bg-white/10 rounded w-full" />
      </Card>
    );
  }

  const obtained = ectsProgression?.ects_obtained || 0;
  const target = ectsProgression?.ects_required || 180.0;
  const percentage = ectsProgression?.progression_percentage || 0;

  return (
    <Card
      onClick={() => navigate('/progression')}
      className="cursor-pointer hover:border-violet-500/40 relative overflow-hidden group flex flex-col justify-between"
    >
      {/* Accent gradient bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-500 to-indigo-500 opacity-60" />

      <div>
        <div className="flex justify-between items-center mb-3">
          <span className="text-xs text-white/40 font-semibold uppercase tracking-wider">ECTS Progression</span>
          <div className="w-8 h-8 rounded-lg bg-violet-500/10 text-violet-400 flex items-center justify-center">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          </div>
        </div>
        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-3xl font-bold text-white leading-none">{obtained.toFixed(1)}</span>
          <span className="text-xs text-white/30 font-medium">/ {target.toFixed(1)} ECTS</span>
        </div>
      </div>

      <ProgressBar
        value={obtained}
        max={target}
        showLabel={true}
        label="Degree Progression"
      />
    </Card>
  );
};

export default ECTSProgressWidget;
