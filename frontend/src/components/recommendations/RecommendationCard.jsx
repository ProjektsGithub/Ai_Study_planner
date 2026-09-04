import { useState } from 'react';
import PropTypes from 'prop-types';
import { useLanguage } from '../../context/LanguageContext';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const RecommendationCard = ({ recommendation, onDismiss }) => {
  const { id, title, description, category, priority, subjectName } = recommendation;
  const { t } = useLanguage();
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');

  const categoryLabels = {
    priority: { label: t('recommendations.cat.priority'), variant: 'violet', icon: '🎯' },
    alert: { label: t('recommendations.cat.alert'), variant: 'error', icon: '⚠️' },
    suggestion: { label: t('recommendations.cat.suggestion'), variant: 'cyan', icon: '⏱️' },
    analysis: { label: t('recommendations.cat.analysis'), variant: 'success', icon: '📈' }
  };

  const cat = categoryLabels[category] || { label: t('recommendations.cat.advice'), variant: 'info', icon: '💡' };

  const handleDismissSubmit = (e) => {
    e.preventDefault();
    onDismiss(id, feedback || 'No comments');
    setShowFeedback(false);
  };

  return (
    <Card className="flex flex-col justify-between h-full border border-slate-200 dark:border-white/10 hover:border-violet-500/30 transition-all duration-300">
      <div>
        {/* Category & Priority Badge Row */}
        <div className="flex items-center justify-between mb-4">
          <Badge variant={cat.variant} icon={cat.icon}>
            {cat.label}
          </Badge>
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-slate-400 dark:text-white/40 uppercase font-semibold">{t('label.priority')}</span>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <span
                  key={star}
                  className={`text-xs ${star <= priority ? 'text-violet-500 dark:text-violet-400' : 'text-slate-300 dark:text-white/10'}`}
                >
                  ★
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Title & Description */}
        <h3 className="text-lg font-bold text-slate-850 dark:text-white mb-2 leading-snug">{title}</h3>
        <p className="text-slate-600 dark:text-white/60 text-sm leading-relaxed mb-4">{description}</p>
      </div>

      <div>
        {/* Subject link if available */}
        {subjectName && (
          <div className="mb-4">
            <a
              href="/subjects"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-600 dark:text-violet-400 hover:text-violet-750 dark:hover:text-violet-300 transition-colors"
            >
              <span>{t('recommendations.related_subject')}</span>
              <span className="px-2 py-0.5 rounded-md bg-violet-50 dark:bg-violet-500/10 border border-violet-200 dark:border-violet-500/20 text-violet-700 dark:text-violet-300">
                {subjectName}
              </span>
            </a>
          </div>
        )}

        {/* Action button / Feedback Form */}
        {!showFeedback ? (
          <div className="flex justify-end border-t border-slate-100 dark:border-white/5 pt-3">
            <button
              onClick={() => setShowFeedback(true)}
              className="text-xs text-slate-400 dark:text-white/40 hover:text-slate-700 dark:hover:text-white/80 transition-colors flex items-center gap-1"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              {t('recommendations.dismiss')}
            </button>
          </div>
        ) : (
          <form onSubmit={handleDismissSubmit} className="border-t border-slate-100 dark:border-white/5 pt-4">
            <p className="text-xs font-semibold text-slate-700 dark:text-white/70 mb-2">{t('recommendations.help_improve')}</p>
            <div className="flex flex-col gap-2">
              <select
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full text-xs px-2 py-1.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-white/10 rounded-lg text-slate-800 dark:text-white"
                required
              >
                <option value="" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">{t('recommendations.reason_placeholder')}</option>
                <option value="already_done" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">{t('recommendations.reason_already_done')}</option>
                <option value="not_relevant" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">{t('recommendations.reason_not_relevant')}</option>
                <option value="too_hard" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">{t('recommendations.reason_too_hard')}</option>
                <option value="other" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">{t('recommendations.reason_other')}</option>
              </select>
              <div className="flex justify-end gap-2 mt-1">
                <button
                  type="button"
                  onClick={() => setShowFeedback(false)}
                  className="px-2.5 py-1 text-[11px] text-slate-400 dark:text-white/50 hover:text-slate-700 dark:hover:text-white transition-colors"
                >
                  {t('action.cancel')}
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-[11px] font-bold text-white bg-violet-600 hover:bg-violet-500 rounded-lg transition-all"
                >
                  {t('action.confirm')}
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
