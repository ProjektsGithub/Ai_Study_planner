import { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";

const TASK_TYPES = [
  { value: "lecture_review",    icon: "📖", label: "Cours",     description: "Revoir le cours",  activeCls: "bg-indigo-600 border-indigo-400 text-white shadow-lg",   inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
  { value: "exercise_practice", icon: "✏️",  label: "Exercices", description: "Pratiquer",        activeCls: "bg-blue-600 border-blue-400 text-white shadow-lg",     inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
  { value: "exam_preparation",  icon: "🔄", label: "Révision",  description: "Préparer l'exam",  activeCls: "bg-emerald-600 border-emerald-400 text-white shadow-lg", inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
  { value: "project_work",      icon: "🚀", label: "Projet",    description: "Avancer",          activeCls: "bg-amber-600 border-amber-400 text-white shadow-lg",   inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
  { value: "reading",           icon: "📰", label: "Lecture",   description: "Lire les docs",    activeCls: "bg-cyan-600 border-cyan-400 text-white shadow-lg",      inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
  { value: "practice",          icon: "🎯", label: "Pratique",  description: "Application",      activeCls: "bg-rose-600 border-rose-400 text-white shadow-lg",      inactiveCls: "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white" },
];

const DAYS = [
  { value: "Monday",    short: "Lun" },
  { value: "Tuesday",   short: "Mar" },
  { value: "Wednesday", short: "Mer" },
  { value: "Thursday",  short: "Jeu" },
  { value: "Friday",    short: "Ven" },
  { value: "Saturday",  short: "Sam" },
  { value: "Sunday",    short: "Dim" },
];

const parseDuration = (start, end) => {
  if (!start || !end) return null;
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  const diff = (eh * 60 + em) - (sh * 60 + sm);
  if (diff <= 0) return null;
  const h = Math.floor(diff / 60);
  const m = diff % 60;
  return { minutes: diff, label: h > 0 ? (m > 0 ? h + "h" + String(m).padStart(2,"0") : h + "h") : m + "min" };
};

const SessionEditor = ({ session, subjects = [], onSave, onDelete, onClose, isOpen }) => {
  const [formData, setFormData] = useState({ subject_id: "", day: "Monday", start_time: "09:00", end_time: "10:00", task_type: "lecture_review", notes: "" });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const t = setTimeout(() => setVisible(true), 10);
      return () => clearTimeout(t);
    } else {
      setVisible(false);
    }
  }, [isOpen]);

  useEffect(() => {
    const norm = (t) => (t ? t.slice(0, 5) : "09:00");
    if (session) {
      setFormData({
        subject_id: session.subject_id || (subjects[0]?.id || ""),
        day: session.day || session.day_of_week || "Monday",
        start_time: norm(session.start_time),
        end_time: norm(session.end_time),
        task_type: session.task_type || "lecture_review",
        notes: session.notes || ""
      });
    } else {
      setFormData({
        subject_id: subjects[0]?.id || "",
        day: "Monday",
        start_time: "09:00",
        end_time: "10:00",
        task_type: "lecture_review",
        notes: ""
      });
    }
    setErrors({});
    setDeleteConfirm(false);
  }, [session, isOpen, subjects]);

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(onClose, 200);
  }, [onClose]);

  const duration = parseDuration(formData.start_time, formData.end_time);
  const durationBadge = !duration
    ? { text: "Horaire invalide", cls: "text-red-400 bg-red-500/10 border-red-500/30" }
    : duration.minutes > 240
      ? { text: duration.label + " · Long", cls: "text-amber-300 bg-amber-500/20 border-amber-500/30" }
      : { text: duration.label, cls: "text-emerald-300 bg-emerald-500/20 border-emerald-500/30" };

  const currentSubject = subjects.find((s) => String(s.id) === String(formData.subject_id));
  const selectedTask = TASK_TYPES.find((t) => t.value === formData.task_type) || TASK_TYPES[0];

  const setField = (field) => (eOrVal) =>
    setFormData((p) => ({ ...p, [field]: eOrVal && eOrVal.target ? eOrVal.target.value : eOrVal }));

  const validate = () => {
    const errs = {};
    if (!formData.subject_id) errs.subject_id = "Sélectionne une matière";
    if (!duration) errs.time = "L'heure de fin doit être après l'heure de début";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      await onSave({
        subject_id: parseInt(formData.subject_id),
        day: formData.day,
        start_time: formData.start_time.length === 5 ? formData.start_time + ":00" : formData.start_time,
        end_time:   formData.end_time.length   === 5 ? formData.end_time   + ":00" : formData.end_time,
        task_type: formData.task_type,
        notes: formData.notes || "",
      });
      handleClose();
    } catch (err) {
      setErrors({ submit: typeof err === 'string' ? err : (err.message || "Une erreur est survenue") });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!session?.id) return;
    setIsSubmitting(true);
    try {
      await onDelete(session.id);
      handleClose();
    } catch (err) {
      setErrors({ submit: typeof err === 'string' ? err : (err.message || "Erreur lors de la suppression") });
      setDeleteConfirm(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-2 sm:p-4" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className={"fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity duration-200 " + (visible ? "opacity-100" : "opacity-0")}
        onClick={handleClose}
      />

      {/* Modal Card */}
      <div
        className={"relative z-10 w-full sm:max-w-lg rounded-3xl border border-slate-700 shadow-2xl transition-all duration-200 text-white overflow-hidden " + (visible ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0")}
        style={{ backgroundColor: "#0f172a", color: "#ffffff", maxHeight: "92vh", overflowY: "auto" }}
      >
        {/* Header */}
        <div className="px-6 pt-5 pb-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center text-xl flex-shrink-0 bg-indigo-500/20 border border-indigo-500/30">
              {selectedTask.icon}
            </div>
            <div className="min-w-0">
              <h3 className="text-lg font-black text-white leading-tight">
                {session ? "Modifier la session" : "Nouvelle session"}
              </h3>
              {currentSubject && <p className="text-xs text-indigo-300 truncate mt-0.5">{currentSubject.name}</p>}
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-all"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-5 space-y-5">
            {/* Matière */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Matière</label>
              <select
                value={formData.subject_id}
                onChange={setField("subject_id")}
                className={"w-full px-3.5 py-2.5 bg-slate-800 border rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all " + (errors.subject_id ? "border-red-500" : "border-slate-700")}
              >
                <option value="" className="bg-slate-800 text-white">— Sélectionner une matière —</option>
                {Array.isArray(subjects) && subjects.map((s) => (
                  <option key={s.id} value={s.id} className="bg-slate-800 text-white">{s.name}</option>
                ))}
              </select>
              {errors.subject_id && <p className="mt-1.5 text-xs text-red-400 font-semibold">{errors.subject_id}</p>}
            </div>

            {/* Type de travail */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Type de travail</label>
              <div className="grid grid-cols-3 gap-2">
                {TASK_TYPES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setFormData((p) => ({ ...p, task_type: t.value }))}
                    className={"flex flex-col items-center gap-1.5 p-3 rounded-2xl border transition-all duration-150 text-center select-none " + (formData.task_type === t.value ? t.activeCls : t.inactiveCls)}
                  >
                    <span className="text-xl leading-none">{t.icon}</span>
                    <span className="text-xs font-bold leading-tight">{t.label}</span>
                    <span className="text-[10px] leading-tight opacity-75 hidden sm:block">{t.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Jour */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Jour de la semaine</label>
              <div className="flex gap-1.5">
                {DAYS.map((d) => (
                  <button
                    key={d.value}
                    type="button"
                    onClick={() => setFormData((p) => ({ ...p, day: d.value }))}
                    className={"flex-1 py-2 rounded-xl text-xs font-bold transition-all duration-150 select-none " + (formData.day === d.value ? "bg-indigo-600 text-white shadow-lg" : "bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 hover:text-white")}
                  >
                    {d.short}
                  </button>
                ))}
              </div>
            </div>

            {/* Horaires */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Horaires</label>
              <div className="flex items-end gap-3">
                <div className="flex-1">
                  <p className="text-xs text-slate-400 mb-1 font-semibold">Début</p>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={setField("start_time")}
                    className="w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="pb-2.5 text-slate-400 text-lg select-none">→</div>
                <div className="flex-1">
                  <p className="text-xs text-slate-400 mb-1 font-semibold">Fin</p>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={setField("end_time")}
                    className="w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className={"flex-shrink-0 px-3 py-2 rounded-xl border text-xs font-bold whitespace-nowrap " + durationBadge.cls}>
                  ⏱ {durationBadge.text}
                </div>
              </div>
              {errors.time && <p className="mt-1.5 text-xs text-red-400 font-semibold">{errors.time}</p>}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Notes <span className="normal-case font-normal text-slate-400">(optionnel)</span>
              </label>
              <textarea
                value={formData.notes}
                onChange={setField("notes")}
                rows={2}
                placeholder="Objectif de la séance..."
                className="w-full px-3.5 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </div>

            {errors.submit && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 flex items-center gap-2">
                <span className="text-red-400">⚠️</span>
                <p className="text-xs font-semibold text-red-300">{errors.submit}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 rounded-b-3xl">
            {deleteConfirm ? (
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-amber-300 min-w-0">
                  <span className="text-sm">⚠️</span>
                  <span className="text-xs font-bold truncate">Supprimer cette session ?</span>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    type="button"
                    onClick={() => setDeleteConfirm(false)}
                    className="px-3 py-2 text-xs font-bold text-slate-300 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700"
                  >
                    Annuler
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isSubmitting}
                    className="px-3 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-500 rounded-xl disabled:opacity-50"
                  >
                    {isSubmitting ? "..." : "Supprimer"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-3">
                <div>
                  {session && (
                    <button
                      type="button"
                      onClick={() => setDeleteConfirm(true)}
                      className="px-3 py-2 text-xs font-bold text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
                    >
                      🗑 Supprimer
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={isSubmitting}
                    className="px-4 py-2.5 text-xs font-bold text-slate-300 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl disabled:opacity-50 shadow-lg shadow-indigo-600/30 transition-all"
                  >
                    {isSubmitting ? "Sauvegarde..." : (session ? "Enregistrer" : "Créer")}
                  </button>
                </div>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

SessionEditor.propTypes = {
  session: PropTypes.object,
  subjects: PropTypes.array,
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  isOpen: PropTypes.bool.isRequired,
};

export default SessionEditor;