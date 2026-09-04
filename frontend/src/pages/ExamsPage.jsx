import { useState, useEffect } from 'react';
import { useAcademicData } from '../context/AcademicDataContext';
import { useLanguage } from '../context/LanguageContext';
import ExamCalendar from '../components/exams/ExamCalendar';
import ExamList from '../components/exams/ExamList';
import ExamForm from '../components/exams/ExamForm';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';

const ExamsPage = () => {
  const {
    exams,
    subjects,
    createExam,
    updateExam,
    deleteExam,
    fetchExams,
    loading
  } = useAcademicData();

  const { t } = useLanguage();

  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchExams();
  }, [fetchExams]);

  const handleAddClick = () => {
    setEditingExam(null);
    setIsModalOpen(true);
  };

  const handleEditClick = (exam) => {
    setEditingExam(exam);
    setIsModalOpen(true);
  };

  const handleDeleteClick = async (id) => {
    if (window.confirm(t('exams.confirm_delete'))) {
      try {
        await deleteExam(id);
      } catch (err) {
        alert(t('exams.delete_error'));
      }
    }
  };

  const handleFormSubmit = async (data) => {
    setSaving(true);
    try {
      if (editingExam) {
        await updateExam(editingExam.id, data);
      } else {
        await createExam(data);
      }
      setIsModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'An error occurred during save.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white mb-1.5">{t('exams.title')}</h1>
          <p className="text-slate-500 dark:text-white/40 text-sm">{t('exams.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* View Toggles */}
          <div className="flex bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 p-1 rounded-xl flex-shrink-0">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${viewMode === 'list' ? 'bg-violet-600 text-white' : 'text-slate-600 dark:text-white/50 hover:text-slate-900 dark:hover:text-white'}`}
            >
              {t('exams.view_list')}
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${viewMode === 'calendar' ? 'bg-violet-600 text-white' : 'text-slate-600 dark:text-white/50 hover:text-slate-900 dark:hover:text-white'}`}
            >
              {t('exams.view_calendar')}
            </button>
          </div>
          <Button onClick={handleAddClick} size="md" className="flex-1 sm:flex-none">
            {t('exams.btn_add')}
          </Button>
        </div>
      </div>

      {loading && exams.length === 0 ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
        </div>
      ) : viewMode === 'calendar' ? (
        <ExamCalendar
          exams={exams}
          onExamClick={handleEditClick}
        />
      ) : (
        <ExamList
          exams={exams}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
        />
      )}

      {/* Add / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingExam ? t('exams.modal_edit_title') : t('exams.modal_add_title')}
        size="lg"
      >
        <ExamForm
          initialData={editingExam}
          subjects={subjects}
          onSubmit={handleFormSubmit}
          onCancel={() => setIsModalOpen(false)}
          saving={saving}
        />
      </Modal>
    </div>
  );
};

export default ExamsPage;
