import { useState } from 'react';
import PropTypes from 'prop-types';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const RecommendationCard = ({ recommendation, onDismiss }) => {
  const { id, title, description, category, priority, subjectId, subjectName } = recommendation;
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');

  const categoryLabels = {
    priority: { label: 'Study Priority', variant: 'violet', icon: '🎯' },
    alert: { label: 'Risk Alert', variant: 'error', icon: '⚠️' },
    suggestion: { label: 'Time Management', variant: 'cyan', icon: '⏱️' },
    analysis: { label: 'Performance Analysis', variant: 'success', icon: '📈' }
  };

  const cat = categoryLabels[category] || { label: 'Advice', variant: 'info', icon: '💡' };

  const handleDismissSubmit = (e) => {
    e.preventDefault();
    onDismiss(id, feedback || 'No comments');
    setShowFeedback(false);
  };

  return (
    <Card className="flex flex-col justify-between h-full border border-white/10 hover:border-violet-500/30 transition-all duration-300">
      <div>
        {/* Category & Priority Badge Row */}
        <div className="flex items-center justify-between mb-4">
          <Badge variant={cat.variant} icon={cat.icon}>
            {cat.label}
          </Badge>
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-white/40 uppercase font-semibold">Priority</span>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <span
                  key={star}
                  className={`text-xs ${star <= priority ? 'text-violet-400' : 'text-white/10'}`}
                >
                  ★
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Title & Description */}
        <h3 className="text-lg font-bold text-white mb-2 leading-snug">{title}</h3>
        <p className="text-white/60 text-sm leading-relaxed mb-4">{description}</p>
      </div>

      <div>
        {/* Subject link if available */}
        {subjectName && (
          <div className="mb-4">
            <a
              href="/subjects"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors"
            >
              <span>Related Subject:</span>
              <span className="px-2 py-0.5 rounded-md bg-violet-500/10 border border-violet-500/20 text-violet-300">
                {subjectName}
              </span>
            </a>
          </div>
        )}

        {/* Action button / Feedback Form */}
        {!showFeedback ? (
          <div className="flex justify-end border-t border-white/5 pt-3">
            <button
              onClick={() => setShowFeedback(true)}
              className="text-xs text-white/40 hover:text-white/80 transition-colors flex items-center gap-1"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Dismiss recommendation
            </button>
          </div>
        ) : (
          <form onSubmit={handleDismissSubmit} className="border-t border-white/5 pt-4">
            <p className="text-xs font-semibold text-white/70 mb-2">Help us improve:</p>
            <div className="flex flex-col gap-2">
              <select
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full text-xs px-2 py-1.5 bg-slate-950/60 border border-white/10 rounded-lg text-white"
                required
              >
                <option value="">Select a reason...</option>
                <option value="already_done">Already done / Completed</option>
                <option value="not_relevant">Not relevant right now</option>
                <option value="too_hard">Too difficult to implement</option>
                <option value="other">Other reason</option>
              </select>
              <div className="flex justify-end gap-2 mt-1">
                <button
                  type="button"
                  onClick={() => setShowFeedback(false)}
                  className="px-2.5 py-1 text-[11px] text-white/50 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-[11px] font-bold text-white bg-violet-600 hover:bg-violet-500 rounded-lg transition-all"
                >
                  Confirm
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </Card>
  );
};

RecommendationCard.propTypes = {
  recommendation: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    category: PropTypes.oneOf(['priority', 'alert', 'suggestion', 'analysis']).isRequired,
    priority: PropTypes.number.isRequired,
    subjectId: PropTypes.number,
    subjectName: PropTypes.string
  }).isRequired,
  onDismiss: PropTypes.func.isRequired
};

export default RecommendationCard;
