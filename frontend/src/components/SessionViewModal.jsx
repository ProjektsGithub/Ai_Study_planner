import React from 'react';
import PropTypes from 'prop-types';
import { useLanguage } from '../context/LanguageContext';

const TASK_ICONS = {
  university_class: '🏛️',
  lecture_review: '📖',
  exercise_practice: '✏️',
  exam_preparation: '🔄',
  project_work: '🚀',
  reading: '📰',
  practice: '🎯',
};

const TASK_BG = {
  university_class: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  lecture_review: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  exercise_practice: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  exam_preparation: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  project_work: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  reading: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  practice: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
};

const parseDurationMin = (start, end) => {
  if (!start || !end) return 60;
  const [sh, sm] = start.split(':').map(Number);
  const [eh, em] = end.split(':').map(Number);
  const diff = (eh * 60 + em) - (sh * 60 + sm);
  return diff > 0 ? diff : 60;
};

const SessionViewModal = ({
  session,
  isOpen,
  onClose,
  onComplete,
  onEdit,
  onDelete
}) => {
  const { t } = useLanguage();

  if (!isOpen || !session) return null;

  const isAcademic = session.is_academic_fixed || session.task_type === 'university_class';
  const icon = TASK_ICONS[session.task_type] || '📖';
  const badgeStyle = TASK_BG[session.task_type] || 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
  const taskLabel = isAcademic
    ? `${t('task.university_class', 'Cours Univ')} (${session.session_type || 'CM/TD'})`
    : t(`task.${session.task_type}`, session.task_type);

  const durationMinutes = parseDurationMin(session.start_time, session.end_time);
  const dayKey = session.day || session.day_of_week;
  const dayLabel = t(`days.${dayKey}`, dayKey);

  const handleCompleteClick = async () => {
    if (onComplete) {
      await onComplete(session);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div
        className="relative z-10 w-full max-w-lg rounded-3xl border border-slate-700 shadow-2xl overflow-hidden text-white transition-all"
        style={{ backgroundColor: '#0f172a', color: '#ffffff' }}
      >
        {/* Top Header Banner */}
        <div className="p-6 border-b border-slate-800 bg-slate-900/60 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-2xl shadow-inner">
              {isAcademic ? '🏛️' : icon}
            </div>
            <div>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-extrabold border mb-1 ${isAcademic ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : badgeStyle}`}>
                {taskLabel}
              </span>
              <h2 className="text-xl font-black text-white leading-tight">
                {session.course_name || session.subject_name || t('session_view.title', 'Détails de la session d\'étude')}
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-all"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5">
          {/* Key info badges */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/60">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">📅 {t('session_view.time_slot', 'Jour & Horaires')}</p>
              <p className="text-sm font-bold text-white mt-1">
                {dayLabel}
              </p>
              <p className="text-xs font-semibold text-indigo-300 mt-0.5">
                ⏱ {session.start_time?.substring(0,5)} - {session.end_time?.substring(0,5)} ({durationMinutes} min)
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/60">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">📍 {t('session_view.activity_type', 'Type & Emplacement')}</p>
              <p className="text-sm font-bold text-white mt-1">
                {isAcademic ? (session.session_type || t('task.university_class', 'Cours Univ')) : taskLabel}
              </p>
              <p className="text-xs font-semibold text-slate-300 mt-0.5 truncate">
                {session.room_location ? `${t('label.room', 'Salle')}: ${session.room_location}` : (isAcademic ? t('task.desc.university_class', 'Cours universitaire') : t('task.practice', 'Séance d\'étude'))}
              </p>
            </div>
          </div>

          {/* Notes section */}
          {session.notes && (
            <div className="p-4 rounded-2xl bg-slate-800/50 border border-slate-700/40">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">📝 {t('session_view.goals_notes', 'Objectifs & Notes')}</p>
              <p className="text-xs text-slate-200 leading-relaxed">{session.notes}</p>
            </div>
          )}

          {/* Academic Notice */}
          {isAcademic && (
            <div className="p-3.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 flex items-center gap-2.5">
              <span>🏛️</span>
              <span>{t('session_view.academic_notice', 'Ce créneau correspond à un cours universitaire fixe de votre emploi du temps.')}</span>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-slate-800 bg-slate-900/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Complete Action Button */}
          {!isAcademic ? (
            <button
              type="button"
              onClick={handleCompleteClick}
              className={`w-full sm:flex-1 py-3 px-4 rounded-2xl font-black text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
                session.completed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30 hover:-translate-y-0.5'
              }`}
            >
              <span>{session.completed ? `✅ ${t('action.completed', 'Terminé')}` : `✅ ${t('action.mark_completed', 'Marquer comme terminé')}`}</span>
              <span className="text-xs font-normal opacity-80">({durationMinutes} min)</span>
            </button>
          ) : (
            <div className="w-full sm:flex-1 text-center py-2 px-3 rounded-xl bg-slate-800 text-xs text-slate-400 font-semibold">
              {t('session_view.academic_notice', 'Présence aux cours scolaires enregistrée')}
            </div>
          )}

          {/* Edit / Close Buttons */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {!isAcademic && onEdit && (
              <button
                type="button"
                onClick={() => { onClose(); onEdit(session); }}
                className="flex-1 sm:flex-initial py-3 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold text-xs transition-all"
              >
                ✏️ {t('action.edit', 'Modifier')}
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="flex-1 sm:flex-initial py-3 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold text-xs transition-all"
            >
              {t('action.close', 'Fermer')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

SessionViewModal.propTypes = {
  session: PropTypes.object,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onComplete: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
};

export default SessionViewModal;
