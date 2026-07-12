import PropTypes from 'prop-types';
import RecommendationCard from './RecommendationCard';

const PriorityList = ({ recommendations = [], onDismiss, activeTab = 'all' }) => {
  // Filters recommendations based on selected category / tab
  const filteredRecs = recommendations.filter((rec) => {
    if (activeTab === 'all') return true;
    return rec.category === activeTab;
  });

  // Sort by priority descending (highest first)
  const sortedRecs = [...filteredRecs].sort((a, b) => b.priority - a.priority);

  if (sortedRecs.length === 0) {
    return (
      <div className="text-center py-16 px-4 border border-white/5 bg-white/[0.01] rounded-2xl">
        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 text-xl">
          💡
        </div>
        <h4 className="text-white font-bold mb-1">No recommendations available</h4>
        <p className="text-white/40 text-sm max-w-xs mx-auto">
          All recommendations for this category have been addressed or hidden.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {sortedRecs.map((rec) => (
        <div key={rec.id} className="h-full">
          <RecommendationCard recommendation={rec} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
};

PriorityList.propTypes = {
  recommendations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      category: PropTypes.string.isRequired,
      priority: PropTypes.number.isRequired,
      subjectId: PropTypes.number,
      subjectName: PropTypes.string
    })
  ).isRequired,
  onDismiss: PropTypes.func.isRequired,
  activeTab: PropTypes.string
};

export default PriorityList;
