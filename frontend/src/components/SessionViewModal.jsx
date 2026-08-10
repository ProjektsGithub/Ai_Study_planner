import React from 'react';
import PropTypes from 'prop-types';

const TASK_LABELS = {
  university_class: { label: 'Cours Universitaire', icon: '🏛️', bg: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  lecture_review:    { label: 'Revoir le cours',    icon: '📖', bg: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' },
  exercise_practice: { label: 'Exercices',         icon: '✏️',  bg: 'bg-orange-500/20 text-orange-300 border-orange-500/30' },
  exam_preparation:  { label: 'Préparation Exam',  icon: '🔄', bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  project_work:      { label: 'Projet',            icon: '🚀', bg: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  reading:           { label: 'Lecture',           icon: '📰', bg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  practice:          { label: 'Pratique',          icon: '🎯', bg: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
};

const DAY_LABELS_FR = {
  Monday: 'Lundi', Tuesday: 'Mardi', Wednesday: 'Mercredi',
  Thursday: 'Jeudi', Friday: 'Vendredi', Saturday: 'Samedi', Sunday: 'Dimanche'
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
  if (!isOpen || !session) return null;

  const isAcademic = session.is_academic_fixed || session.task_type === 'university_class';
  const taskInfo = TASK_LABELS[session.task_type] || TASK_LABELS.lecture_review;
  const durationMinutes = parseDurationMin(session.start_time, session.end_time);

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
              {isAcademic ? '🏛️' : taskInfo.icon}
            </div>
            <div>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-extrabold border mb-1 ${isAcademic ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : taskInfo.bg}`}>
                {isAcademic ? `Cours Fixe (${session.session_type || 'CM/TD'})` : taskInfo.label}
              </span>
              <h2 className="text-xl font-black text-white leading-tight">
                {session.course_name || session.subject_name || 'Session d\'Étude'}
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
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">📅 Jour & Horaires</p>
              <p className="text-sm font-bold text-white mt-1">
                {DAY_LABELS_FR[session.day || session.day_of_week] || session.day}
              </p>
              <p className="text-xs font-semibold text-indigo-300 mt-0.5">
                ⏱ {session.start_time?.substring(0,5)} - {session.end_time?.substring(0,5)} ({durationMinutes} min)
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/60">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">📍 Type & Emplacement</p>
              <p className="text-sm font-bold text-white mt-1">
                {isAcademic ? (session.session_type || 'Cours Magistral') : (session.task_type || 'Révision IA')}
              </p>
              <p className="text-xs font-semibold text-slate-300 mt-0.5 truncate">
                {session.room_location ? `Salle: ${session.room_location}` : 'Séance programmée'}
              </p>
            </div>
          </div>

          {/* Notes section */}
          {session.notes && (
            <div className="p-4 rounded-2xl bg-slate-800/50 border border-slate-700/40">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">📝 Notes & Consignes</p>
              <p className="text-xs text-slate-200 leading-relaxed">{session.notes}</p>
            </div>
          )}

          {/* Academic Notice */}
          {isAcademic && (
            <div className="p-3.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 flex items-center gap-2.5">
              <span>🏛️</span>
              <span>Ceci est un cours universitaire obligatoire fixé par votre filière.</span>
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
              <span>{session.completed ? '✅ Déjà Effectué' : '✅ Marquer comme fait'}</span>
              <span className="text-xs font-normal opacity-80">({durationMinutes} min)</span>
            </button>
          ) : (
            <div className="w-full sm:flex-1 text-center py-2 px-3 rounded-xl bg-slate-800 text-xs text-slate-400 font-semibold">
              Présence aux cours scolaires enregistrée
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
                ✏️ Modifier
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="flex-1 sm:flex-initial py-3 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold text-xs transition-all"
            >
              Fermer
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
