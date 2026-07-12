import PropTypes from 'prop-types';

const ECTSBreakdown = ({ breakdown = [] }) => {
  const semesters = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'];

  return (
    <div className="space-y-4">
      {semesters.map((sem) => {
        const data = breakdown.find((b) => b.semester === sem) || { obtained: 0, total: 30 };
        const obtained = data.obtained || 0;
        const total = data.total || 30; // standard European semester target is 30 ECTS
        const percentage = total > 0 ? Math.min(Math.round((obtained / total) * 100), 100) : 0;

        return (
          <div key={sem} className="p-4 rounded-xl border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] transition-colors">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-white">{sem}</span>
              <span className="text-xs text-white/50">
                <span className="text-violet-400 font-bold">{obtained.toFixed(1)}</span> / {total.toFixed(1)} ECTS
              </span>
            </div>

            {/* Horizontal progress bar */}
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
              <div
                className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

ECTSBreakdown.propTypes = {
  breakdown: PropTypes.arrayOf(
    PropTypes.shape({
      semester: PropTypes.string.isRequired,
      obtained: PropTypes.number.isRequired,
      total: PropTypes.number.isRequired,
    })
  ),
};

export default ECTSBreakdown;
