import PropTypes from 'prop-types';
import { useLanguage } from '../../context/LanguageContext';
import ExamCard from './ExamCard';

const ExamList = ({ exams = [], onEdit, onDelete }) => {
  const { t } = useLanguage();

  if (exams.length === 0) {
    return (
      <div className="empty-state text-center py-16">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-white/5 flex items-center justify-center mx-auto mb-4">
          <svg className="w-7 h-7 text-slate-400 dark:text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 className="text-slate-700 dark:text-white/60 font-medium mb-1">{t('exams.no_exams')}</h3>
        <p className="text-slate-400 dark:text-white/30 text-sm">{t('exams.no_exams_sub')}</p>
      </div>
    );
  }

  // Sort chronologically
  const sortedExams = [...exams].sort((a, b) => new Date(a.exam_date) - new Date(b.exam_date));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
      {sortedExams.map((exam) => (
        <ExamCard
          key={exam.id}
          exam={exam}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};

ExamList.propTypes = {
  exams: PropTypes.array.isRequired,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default ExamList;
