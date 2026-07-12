import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DAY_LABELS = {
  Monday: 'Monday', Tuesday: 'Tuesday', Wednesday: 'Wednesday',
  Thursday: 'Thursday', Friday: 'Friday', Saturday: 'Saturday', Sunday: 'Sunday',
};
const DAY_ABBR = {
  Monday: 'Mo', Tuesday: 'Tu', Wednesday: 'We',
  Thursday: 'Th', Friday: 'Fr', Saturday: 'Sa', Sunday: 'Su',
};

const ENERGY_CONFIG = {
  high: { label: 'High', color: 'text-emerald-400', dot: 'bg-emerald-400' },
  medium: { label: 'Medium', color: 'text-amber-400', dot: 'bg-amber-400' },
  low: { label: 'Low', color: 'text-red-400', dot: 'bg-red-400' },
};

const AvailabilityManager = () => {
  const [availabilities, setAvailabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAvailability, setEditingAvailability] = useState(null);
  const [formData, setFormData] = useState({ day_of_week: 'Monday', start_time: '09:00', end_time: '17:00', energy_level: '' });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const loadAvailabilities = async () => {
    try {
      const response = await apiClient.get('/api/v1/availabilities');
      setAvailabilities(response.data.availabilities || []);
    } catch (error) {
      console.error('Error loading availabilities:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAvailabilities(); }, []);

  const handleAdd = () => {
    setEditingAvailability(null);
    setFormData({ day_of_week: 'Monday', start_time: '09:00', end_time: '17:00', energy_level: '' });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleEdit = (av) => {
    setEditingAvailability(av);
    setFormData({
      day_of_week: av.day_of_week,
      start_time: av.start_time.substring(0, 5),
      end_time: av.end_time.substring(0, 5),
      energy_level: av.energy_level || '',
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this availability slot?')) return;
    try {
      await apiClient.delete(`/api/v1/availabilities/${id}`);
      setAvailabilities((prev) => prev.filter((a) => a.id !== id));
    } catch (error) {
      alert(error.response?.data?.detail || 'Error deleting availability slot');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (formData.start_time >= formData.end_time) newErrors.end_time = 'End time must be after start time';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSaving(true);
    try {
      const payload = {
        day_of_week: formData.day_of_week,
        start_time: formData.start_time + ':00',
        end_time: formData.end_time + ':00',
        energy_level: formData.energy_level === '' ? null : formData.energy_level,
      };
      if (editingAvailability) {
        const res = await apiClient.put(`/api/v1/availabilities/${editingAvailability.id}`, payload);
        setAvailabilities((prev) => prev.map((a) => a.id === editingAvailability.id ? res.data : a));
      } else {
        const res = await apiClient.post('/api/v1/availabilities', payload);
        setAvailabilities((prev) => [...prev, res.data]);
      }
      setIsModalOpen(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Error saving availability');
    } finally {
      setSaving(false);
    }
  };

  const grouped = DAYS_OF_WEEK.reduce((acc, day) => {
    acc[day] = availabilities.filter((a) => a.day_of_week === day);
    return acc;
  }, {});

  const totalHours = availabilities.reduce((sum, a) => {
    const [sh, sm] = a.start_time.split(':').map(Number);
    const [eh, em] = a.end_time.split(':').map(Number);
    return sum + (eh + em / 60 - sh - sm / 60);
  }, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-10 h-10 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">My Availabilities</h2>
          <p className="text-white/40 text-sm mt-1">
            {availabilities.length} slot(s) · <span className="text-cyan-400">{totalHours.toFixed(1)}h</span> available / week
          </p>
        </div>
        <Button onClick={handleAdd}>+ Add Availability</Button>
      </div>

      {availabilities.length === 0 ? (
        <div className="empty-state">
          <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-white/60 font-medium mb-1">No availabilities defined</h3>
          <p className="text-white/30 text-sm">Define your available study time slots.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {DAYS_OF_WEEK.map((day) => {
            const slots = grouped[day];
            if (slots.length === 0) return null;
            return (
              <div key={day} className="rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-md overflow-hidden hover:border-violet-500/20 transition-all duration-300">
                {/* Day header */}
                <div className="px-4 py-3 border-b border-white/8 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
                      <span className="text-xs font-bold text-violet-400">{DAY_ABBR[day]}</span>
                    </div>
                    <span className="font-semibold text-white text-sm">{DAY_LABELS[day]}</span>
                  </div>
                  <span className="text-xs text-white/30">{slots.length} slot{slots.length > 1 ? 's' : ''}</span>
                </div>
                <div className="p-3 space-y-2">
                  {slots.map((av) => {
                    const energy = ENERGY_CONFIG[av.energy_level];
                    return (
                      <div key={av.id} className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 group transition-all">
                        <div className="flex items-center gap-2.5">
                          <svg className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <span className="text-xs font-semibold text-white">
                              {av.start_time.substring(0, 5)} – {av.end_time.substring(0, 5)}
                            </span>
                            {energy && (
                              <div className="flex items-center gap-1 mt-0.5">
                                <div className={`w-1.5 h-1.5 rounded-full ${energy.dot}`} />
                                <span className={`text-[10px] ${energy.color}`}>{energy.label}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleEdit(av)} className="p-1 rounded text-white/30 hover:text-violet-400 hover:bg-violet-500/10 transition-all" aria-label="Edit">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button onClick={() => handleDelete(av.id)} className="p-1 rounded text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all" aria-label="Delete">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Days with no slots — show faded */}
          {DAYS_OF_WEEK.filter((day) => grouped[day].length === 0).map((day) => (
            <div
              key={day}
              onClick={handleAdd}
              className="rounded-2xl border border-dashed border-white/8 bg-white/[0.02] p-4 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-violet-500/30 hover:bg-white/[0.04] transition-all min-h-[100px] group"
            >
              <span className="text-xs text-white/20 group-hover:text-violet-400/60 transition-colors font-medium">{DAY_LABELS[day]}</span>
              <span className="text-xs text-white/15 group-hover:text-white/30 transition-colors">+ Add Slot</span>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingAvailability ? 'Edit Availability Slot' : 'New Availability Slot'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Day of the Week *</label>
            <select name="day_of_week" value={formData.day_of_week} onChange={handleChange} required>
              {DAYS_OF_WEEK.map((day) => <option key={day} value={day}>{DAY_LABELS[day]}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input label="Start Time *" type="time" name="start_time" value={formData.start_time} onChange={handleChange} error={errors.start_time} required />
            <Input label="End Time *" type="time" name="end_time" value={formData.end_time} onChange={handleChange} error={errors.end_time} required />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-1.5">Energy Level</label>
            <select name="energy_level" value={formData.energy_level} onChange={handleChange}>
              <option value="">Unspecified</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <p className="text-xs text-white/30 mt-1">Your typical energy level during this time slot</p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" variant="primary" loading={saving} disabled={saving}>
              {editingAvailability ? 'Save' : 'Add'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AvailabilityManager;
