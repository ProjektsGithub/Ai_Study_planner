import { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";

const TASK_TYPES = [
  { value: "lecture_review",    icon: "📖", label: "Cours",     description: "Revoir le cours",  activeCls: "bg-violet-500/20 border-violet-400/60 text-violet-200",   inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-violet-500/30 hover:bg-violet-500/5" },
  { value: "exercise_practice", icon: "✏️",  label: "Exercices", description: "Pratiquer",        activeCls: "bg-blue-500/20 border-blue-400/60 text-blue-200",         inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-blue-500/30 hover:bg-blue-500/5" },
  { value: "exam_preparation",  icon: "🔄", label: "Révision",  description: "Préparer l'exam",  activeCls: "bg-emerald-500/20 border-emerald-400/60 text-emerald-200", inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-emerald-500/30 hover:bg-emerald-500/5" },
  { value: "project_work",      icon: "🚀", label: "Projet",    description: "Avancer",          activeCls: "bg-amber-500/20 border-amber-400/60 text-amber-200",       inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-amber-500/30 hover:bg-amber-500/5" },
  { value: "reading",           icon: "📰", label: "Lecture",   description: "Lire les docs",    activeCls: "bg-cyan-500/20 border-cyan-400/60 text-cyan-200",          inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-cyan-500/30 hover:bg-cyan-500/5" },
  { value: "practice",          icon: "🎯", label: "Pratique",  description: "Application",      activeCls: "bg-rose-500/20 border-rose-400/60 text-rose-200",          inactiveCls: "bg-white/[0.03] border-white/10 text-white/50 hover:border-rose-500/30 hover:bg-rose-500/5" },
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
  const [formData, setFormData] = useState({ subject_id: "", day: "Monday", start_time: "09:00", end_time: "10:00", task_type: "lecture", notes: "" });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isOpen) { const t = setTimeout(() => setVisible(true), 10); return () => clearTimeout(t); }
    else { setVisible(false); }
  }, [isOpen]);

  useEffect(() => {
    const norm = (t) => (t ? t.slice(0, 5) : "09:00");
    if (session) {
      setFormData({ subject_id: session.subject_id || "", day: session.day || session.day_of_week || "Monday", start_time: norm(session.start_time), end_time: norm(session.end_time), task_type: session.task_type || "lecture", notes: session.notes || "" });
    } else {
      setFormData({ subject_id: subjects[0]?.id || "", day: "Monday", start_time: "09:00", end_time: "10:00", task_type: "lecture", notes: "" });
    }
    setErrors({});
    setDeleteConfirm(false);
  }, [session, isOpen, subjects]);

  const handleClose = useCallback(() => { setVisible(false); setTimeout(onClose, 200); }, [onClose]);

  const duration = parseDuration(formData.start_time, formData.end_time);
  const durationBadge = !duration
    ? { text: "Horaire invalide", cls: "text-red-400 bg-red-500/10 border-red-500/20" }
    : duration.minutes > 240
      ? { text: duration.label + " · Long", cls: "text-amber-400 bg-amber-500/10 border-amber-500/20" }
      : { text: duration.label, cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" };

  const currentSubject = subjects.find((s) => String(s.id) === String(formData.subject_id));
  const selectedTask = TASK_TYPES.find((t) => t.value === formData.task_type) || TASK_TYPES[0];
  // Helper: update a field from an input event OR a direct value
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
      setErrors({ submit: err.message || "Une erreur est survenue" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!session?.id) return;
    setIsSubmitting(true);
    try { await onDelete(session.id); handleClose(); }
    catch (err) { setErrors({ submit: err.message || "Erreur lors de la suppression" }); setDeleteConfirm(false); }
    finally { setIsSubmitting(false); }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center" role="dialog" aria-modal="true">
      <div className={"fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity duration-200 " + (visible ? "opacity-100" : "opacity-0")} onClick={handleClose} />
      <div className={"relative z-10 w-full sm:max-w-lg sm:mx-4 bg-slate-900 border border-white/10 rounded-t-3xl sm:rounded-2xl shadow-2xl transition-all duration-200 " + (visible ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0")} style={{ maxHeight: "92vh", overflowY: "auto" }}>
        <div className="flex justify-center pt-3 pb-1 sm:hidden"><div className="w-10 h-1 rounded-full bg-white/20" /></div>

        {/* Header */}
        <div className="px-6 pt-4 pb-4 border-b border-white/5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-xl flex-shrink-0 bg-white/5">{selectedTask.icon}</div>
            <div className="min-w-0">
              <h3 className="text-base font-bold text-white leading-tight">{session ? "Modifier la session" : "Nouvelle session"}</h3>
              {currentSubject && <p className="text-xs text-white/40 truncate mt-0.5">{currentSubject.name}</p>}
            </div>
          </div>
          <button type="button" onClick={handleClose} className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white transition-all">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-5 space-y-6">

            {/* Matière */}
            <div>
              <label className="block text-[10px] font-bold text-white/35 uppercase tracking-widest mb-2">Matière</label>
              <select value={formData.subject_id} onChange={setField("subject_id")} className={"w-full px-3.5 py-2.5 bg-white/5 border rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all " + (errors.subject_id ? "border-red-500/50" : "border-white/10")}>
                <option value="">— Sélectionner une matière —</option>
                {Array.isArray(subjects) && subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              {errors.subject_id && <p className="mt-1.5 text-xs text-red-400">{errors.subject_id}</p>}
            </div>

            {/* Type de travail */}
            <div>
              <label className="block text-[10px] font-bold text-white/35 uppercase tracking-widest mb-2">Type de travail</label>
              <div className="grid grid-cols-3 gap-2">
                {TASK_TYPES.map((t) => (
                  <button key={t.value} type="button" onClick={() => setFormData((p) => ({ ...p, task_type: t.value }))}
                    className={"flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all duration-150 text-center select-none " + (formData.task_type === t.value ? t.activeCls : t.inactiveCls)}>
                    <span className="text-xl leading-none">{t.icon}</span>
                    <span className="text-[11px] font-bold leading-tight">{t.label}</span>
                    <span className="text-[9px] leading-tight opacity-60 hidden sm:block">{t.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Jour */}
            <div>
              <label className="block text-[10px] font-bold text-white/35 uppercase tracking-widest mb-2">Jour de la semaine</label>
              <div className="flex gap-1">
                {DAYS.map((d) => (
                  <button key={d.value} type="button" onClick={() => setFormData((p) => ({ ...p, day: d.value }))}
                    className={"flex-1 py-2 rounded-xl text-[11px] font-bold transition-all duration-150 select-none " + (formData.day === d.value ? "bg-violet-600 text-white shadow-glow-sm" : "bg-white/5 text-white/45 border border-white/10 hover:border-violet-500/40 hover:text-white/80")}>
                    {d.short}
                  </button>
                ))}
              </div>
            </div>

            {/* Horaires */}
            <div>
              <label className="block text-[10px] font-bold text-white/35 uppercase tracking-widest mb-2">Horaires</label>
              <div className="flex items-end gap-3">
                <div className="flex-1">
                  <p className="text-[10px] text-white/30 mb-1">Début</p>
                  <input type="time" value={formData.start_time} onChange={setField("start_time")} className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all" />
                </div>
                <div className="pb-2.5 text-white/20 text-lg select-none">→</div>
                <div className="flex-1">
                  <p className="text-[10px] text-white/30 mb-1">Fin</p>
                  <input type="time" value={formData.end_time} onChange={setField("end_time")} className="w-full px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all" />
                </div>
                <div className={"flex-shrink-0 px-2.5 py-2 rounded-xl border text-[11px] font-bold whitespace-nowrap " + durationBadge.cls}>⏱ {durationBadge.text}</div>
              </div>
              {errors.time && <p className="mt-1.5 text-xs text-red-400">{errors.time}</p>}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-[10px] font-bold text-white/35 uppercase tracking-widest mb-2">Notes <span className="normal-case font-normal opacity-50">(optionnel)</span></label>
              <textarea value={formData.notes} onChange={setField("notes")} rows={2} placeholder="Que veux-tu accomplir pendant cette session ?" className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder-white/20 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all resize-none" />
            </div>

            {errors.submit && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <p className="text-sm text-red-400">{errors.submit}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-white/5 bg-slate-950/30 rounded-b-3xl sm:rounded-b-2xl">
            {deleteConfirm ? (
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-amber-400 min-w-0">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  <span className="text-sm font-semibold truncate">Supprimer cette session ?</span>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button type="button" onClick={() => setDeleteConfirm(false)} className="px-3 py-1.5 text-xs font-semibold text-white/60 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-all">Non, garder</button>
                  <button type="button" onClick={handleDelete} disabled={isSubmitting} className="px-3 py-1.5 text-xs font-bold text-white bg-red-600 hover:bg-red-500 rounded-lg disabled:opacity-50 transition-all">{isSubmitting ? "..." : "Supprimer"}</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-3">
                <div>
                  {session && (
                    <button type="button" onClick={() => setDeleteConfirm(true)} className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                      Supprimer
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={handleClose} disabled={isSubmitting} className="px-4 py-2 text-sm font-semibold text-white/60 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 disabled:opacity-50 transition-all">Annuler</button>
                  <button type="submit" disabled={isSubmitting} className="flex items-center gap-2 px-5 py-2 text-sm font-bold text-white bg-gradient-to-r from-violet-600 to-indigo-500 rounded-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none transition-all shadow-lg shadow-violet-500/20">
                    {isSubmitting ? (
                      <><svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Sauvegarde...</>
                    ) : (
                      <><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>{session ? "Enregistrer" : "Créer"}</>
                    )}
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
  session: PropTypes.shape({ id: PropTypes.number, subject_id: PropTypes.number, day: PropTypes.string, day_of_week: PropTypes.string, start_time: PropTypes.string, end_time: PropTypes.string, task_type: PropTypes.string, notes: PropTypes.string }),
  subjects: PropTypes.arrayOf(PropTypes.shape({ id: PropTypes.number.isRequired, name: PropTypes.string.isRequired })),
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  isOpen: PropTypes.bool.isRequired,
};

export default SessionEditor;