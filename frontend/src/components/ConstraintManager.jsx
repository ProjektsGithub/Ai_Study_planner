import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

const CONSTRAINT_TYPES = {
  forbidden_slot: 'Forbidden Slot',
  max_daily_hours: 'Max Hours / Day',
  required_break: 'Required Break',
  fixed_slot: 'Fixed Slot',
};

const CONSTRAINT_ICONS = {
  forbidden_slot: { icon: '🚫', color: 'from-red-600/30 to-red-600/5', badge: 'bg-red-500/15 text-red-300 border border-red-500/25', topBar: 'from-red-500 to-red-400' },
  max_daily_hours: { icon: '⏱', color: 'from-amber-600/30 to-amber-600/5', badge: 'bg-amber-500/15 text-amber-300 border border-amber-500/25', topBar: 'from-amber-500 to-amber-400' },
  required_break: { icon: '☕', color: 'from-emerald-600/30 to-emerald-600/5', badge: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25', topBar: 'from-emerald-500 to-emerald-400' },
  fixed_slot: { icon: '📌', color: 'from-blue-600/30 to-blue-600/5', badge: 'bg-blue-500/15 text-blue-300 border border-blue-500/25', topBar: 'from-blue-500 to-blue-400' },
};

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DAY_LABELS = {
  Monday: 'Monday', Tuesday: 'Tuesday', Wednesday: 'Wednesday',
  Thursday: 'Thursday', Friday: 'Friday', Saturday: 'Saturday', Sunday: 'Sunday',
};

const ConstraintManager = () => {
  const [constraints, setConstraints] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConstraint, setEditingConstraint] = useState(null);
  const [formData, setFormData] = useState({
    constraint_type: 'forbidden_slot', active: true,
    day_of_week: 'Monday', start_time: '12:00', end_time: '13:00',
    subject_id: '', max_hours: 8, duration_minutes: 15, after_minutes: 120,
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const loadConstraints = async () => {
    try {
      const res = await apiClient.get('/api/v1/constraints');
      setConstraints(res.data.constraints || []);
    } catch (error) { console.error(error); } finally { setLoading(false); }
  };

  const loadSubjects = async () => {
    try {
      const res = await apiClient.get('/api/v1/subjects');
      setSubjects(res.data || []);
    } catch (error) { console.error(error); }
  };

  useEffect(() => { loadConstraints(); loadSubjects(); }, []);

  const defaultForm = {
    constraint_type: 'forbidden_slot', active: true,
    day_of_week: 'Monday', start_time: '12:00', end_time: '13:00',
    subject_id: '', max_hours: 8, duration_minutes: 15, after_minutes: 120,
  };

  const handleAdd = () => { setEditingConstraint(null); setFormData(defaultForm); setErrors({}); setIsModalOpen(true); };

  const handleEdit = (c) => {
    setEditingConstraint(c);
    const p = c.parameters;
    setFormData({
      constraint_type: c.constraint_type, active: c.active,
      day_of_week: p.day_of_week || 'Monday',
      start_time: p.start_time ? p.start_time.substring(0, 5) : '12:00',
      end_time: p.end_time ? p.end_time.substring(0, 5) : '13:00',
      subject_id: p.subject_id || '', max_hours: p.max_hours || 8,
      duration_minutes: p.duration_minutes || 15, after_minutes: p.after_minutes || 120,
    });
    setErrors({}); setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this constraint?')) return;
    try {
      await apiClient.delete(`/api/v1/constraints/${id}`);
      setConstraints((prev) => prev.filter((c) => c.id !== id));
    } catch (error) { alert(error.response?.data?.detail || 'Error deleting constraint'); }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked :
        ['max_hours', 'duration_minutes', 'after_minutes', 'subject_id'].includes(name)
          ? (value === '' ? '' : parseFloat(value)) : value,
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validateForm = () => {
    const newErrors = {};
    const type = formData.constraint_type;
    if (['forbidden_slot', 'fixed_slot'].includes(type)) {
      if (formData.start_time >= formData.end_time) newErrors.end_time = 'End time must be after start time';
      if (type === 'fixed_slot' && !formData.subject_id) newErrors.subject_id = 'Subject is required';
    }
    if (type === 'max_daily_hours' && (formData.max_hours < 1 || formData.max_hours > 24)) newErrors.max_hours = 'Must be between 1 and 24 hours';
    if (type === 'required_break') {
      if (formData.duration_minutes < 5 || formData.duration_minutes > 120) newErrors.duration_minutes = 'Must be between 5 and 120 min';
      if (formData.after_minutes < 30 || formData.after_minutes > 240) newErrors.after_minutes = 'Must be between 30 and 240 min';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSaving(true);
    try {
      let parameters = {};
      switch (formData.constraint_type) {
        case 'forbidden_slot': parameters = { day_of_week: formData.day_of_week, start_time: formData.start_time + ':00', end_time: formData.end_time + ':00' }; break;
        case 'max_daily_hours': parameters = { max_hours: formData.max_hours }; break;
        case 'required_break': parameters = { duration_minutes: formData.duration_minutes, after_minutes: formData.after_minutes }; break;
        case 'fixed_slot': parameters = { day_of_week: formData.day_of_week, start_time: formData.start_time + ':00', end_time: formData.end_time + ':00', subject_id: formData.subject_id }; break;
      }
      const payload = { constraint_type: formData.constraint_type, parameters, active: formData.active };
      if (editingConstraint) {
        const res = await apiClient.put(`/api/v1/constraints/${editingConstraint.id}`, payload);
        setConstraints((prev) => prev.map((c) => c.id === editingConstraint.id ? res.data : c));
      } else {
        const res = await apiClient.post('/api/v1/constraints', payload);
        setConstraints((prev) => [...prev, res.data]);
      }
      setIsModalOpen(false);
    } catch (error) { alert(error.response?.data?.detail || 'Error saving constraint'); } finally { setSaving(false); }
  };

  const toggleActive = async (constraint) => {
    try {
      const res = await apiClient.put(`/api/v1/constraints/${constraint.id}`, { active: !constraint.active });
      setConstraints((prev) => prev.map((c) => c.id === constraint.id ? res.data : c));
    } catch (error) { alert(error.response?.data?.detail || 'Error'); }
  };

  const getDescription = (c) => {
    const p = c.parameters;
    switch (c.constraint_type) {
      case 'forbidden_slot': return `${DAY_LABELS[p.day_of_week]} · ${p.start_time?.substring(0, 5)} – ${p.end_time?.substring(0, 5)}`;
      case 'max_daily_hours': return `Maximum ${p.max_hours}h per day`;
      case 'required_break': return `Break of ${p.duration_minutes}min every ${p.after_minutes}min`;
      case 'fixed_slot': { const sub = subjects.find((s) => s.id === p.subject_id); return `${DAY_LABELS[p.day_of_week]} · ${p.start_time?.substring(0, 5)} – ${p.end_time?.substring(0, 5)} (${sub?.name || '?'})`; }
      default: return 'Constraint';
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-10 h-10 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">My Constraints</h2>
          <p className="text-white/40 text-sm mt-1">
            {constraints.length} constraint(s) · <span className="text-emerald-400">{constraints.filter((c) => c.active).length} active</span>
          </p>
        </div>
        <Button onClick={handleAdd}>+ Add Constraint</Button>
      </div>

      {constraints.length === 0 ? (
        <div className="empty-state">
          <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 text-2xl">⚙️</div>
          <h3 className="text-white/60 font-medium mb-1">No constraints defined</h3>
          <p className="text-white/30 text-sm">Add constraints to customize your study plan schedule.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {constraints.map((constraint) => {
            const cfg = CONSTRAINT_ICONS[constraint.constraint_type] || CONSTRAINT_ICONS.forbidden_slot;
            return (
              <div
                key={constraint.id}
                className={`relative rounded-2xl border border-white/10 bg-gradient-to-br ${cfg.color} backdrop-blur-md p-4 transition-all duration-300 hover:border-white/20 ${!constraint.active ? 'opacity-50' : ''}`}
              >
                <div className={`absolute top-0 left-5 right-5 h-0.5 rounded-b-full bg-gradient-to-r ${cfg.topBar} opacity-60`} />
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-xl mt-0.5">{cfg.icon}</span>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${cfg.badge}`}>
                          {CONSTRAINT_TYPES[constraint.constraint_type]}
                        </span>
                        {!constraint.active && (
                          <span className="px-2 py-0.5 rounded-full text-xs bg-white/10 text-white/40">Disabled</span>
                        )}
                      </div>
                      <p className="text-sm text-white/80 font-medium">{getDescription(constraint)}</p>
                    </div>
                  </div>
                  <div className="flex gap-1.5 ml-4">
                    <button
                      onClick={() => toggleActive(constraint)}
                      title={constraint.active ? 'Disable' : 'Enable'}
                      className={`p-1.5 rounded-lg transition-all ${constraint.active ? 'text-emerald-400 hover:bg-emerald-500/10' : 'text-white/30 hover:bg-white/8'}`}
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button onClick={() => handleEdit(constraint)} className="p-1.5 rounded-lg text-white/30 hover:text-violet-400 hover:bg-violet-500/10 transition-all" aria-label="Edit">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button onClick={() => handleDelete(constraint.id)} className="p-1.5 rounded-lg text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all" aria-label="Delete">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingConstraint ? 'Edit Constraint' : 'New Constraint'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Constraint Type *</label>
            <select name="constraint_type" value={formData.constraint_type} onChange={handleChange} required disabled={!!editingConstraint}>
              {Object.entries(CONSTRAINT_TYPES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>

          {['forbidden_slot', 'fixed_slot'].includes(formData.constraint_type) && (
            <>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-1.5">Day of the Week *</label>
                <select name="day_of_week" value={formData.day_of_week} onChange={handleChange} required>
                  {DAYS_OF_WEEK.map((d) => <option key={d} value={d}>{DAY_LABELS[d]}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Start Time *" type="time" name="start_time" value={formData.start_time} onChange={handleChange} error={errors.start_time} required />
                <Input label="End Time *" type="time" name="end_time" value={formData.end_time} onChange={handleChange} error={errors.end_time} required />
              </div>
              {formData.constraint_type === 'fixed_slot' && (
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-1.5">Subject *</label>
                  <select name="subject_id" value={formData.subject_id} onChange={handleChange} required>
                    <option value="">Select a subject</option>
                    {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                  {errors.subject_id && <p className="mt-1 text-xs text-red-400">{errors.subject_id}</p>}
                </div>
              )}
            </>
          )}

          {formData.constraint_type === 'max_daily_hours' && (
            <Input label="Maximum Hours per Day *" type="number" name="max_hours" value={formData.max_hours} onChange={handleChange} min="1" max="24" step="0.5" error={errors.max_hours} required />
          )}

          {formData.constraint_type === 'required_break' && (
            <>
              <Input label="Break Duration (minutes) *" type="number" name="duration_minutes" value={formData.duration_minutes} onChange={handleChange} min="5" max="120" error={errors.duration_minutes} required />
              <Input label="Frequency (every X minutes) *" type="number" name="after_minutes" value={formData.after_minutes} onChange={handleChange} min="30" max="240" error={errors.after_minutes} required />
            </>
          )}

          <label className="flex items-center gap-3 cursor-pointer group">
            <input type="checkbox" name="active" checked={formData.active} onChange={handleChange} />
            <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">Active constraint</span>
          </label>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" variant="primary" loading={saving} disabled={saving}>
              {editingConstraint ? 'Save' : 'Add'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ConstraintManager;
