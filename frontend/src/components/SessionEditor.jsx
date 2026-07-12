import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * SessionEditor Component
 * Modal for editing or creating study sessions
 */
const SessionEditor = ({ 
  session, 
  subjects = [],
  onSave, 
  onDelete,
  onClose,
  isOpen 
}) => {
  const [formData, setFormData] = useState({
    subject_id: '',
    day_of_week: 'Monday',
    start_time: '09:00',
    end_time: '10:00',
    task_type: 'lecture',
    notes: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const taskTypes = [
    { value: 'lecture', label: 'Lecture' },
    { value: 'exercise', label: 'Exercises' },
    { value: 'revision', label: 'Revision' },
    { value: 'project', label: 'Project' },
    { value: 'reading', label: 'Reading' },
    { value: 'practice', label: 'Practice' }
  ];

  // Initialize form with session data if editing
  useEffect(() => {
    if (session) {
      setFormData({
        subject_id: session.subject_id || '',
        day_of_week: session.day_of_week || 'Monday',
        start_time: session.start_time || '09:00',
        end_time: session.end_time || '10:00',
        task_type: session.task_type || 'lecture',
        notes: session.notes || ''
      });
    } else {
      // Reset form for new session
      setFormData({
        subject_id: '',
        day_of_week: 'Monday',
        start_time: '09:00',
        end_time: '10:00',
        task_type: 'lecture',
        notes: ''
      });
    }
    setErrors({});
  }, [session, isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.subject_id) {
      newErrors.subject_id = 'Please select a subject';
    }

    if (!formData.start_time) {
      newErrors.start_time = 'Start time is required';
    }

    if (!formData.end_time) {
      newErrors.end_time = 'End time is required';
    }

    // Validate time format (HH:MM)
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
    if (formData.start_time && !timeRegex.test(formData.start_time)) {
      newErrors.start_time = 'Invalid format (HH:MM)';
    }

    if (formData.end_time && !timeRegex.test(formData.end_time)) {
      newErrors.end_time = 'Invalid format (HH:MM)';
    }

    // Validate start_time < end_time
    if (formData.start_time && formData.end_time) {
      const [startHour, startMin] = formData.start_time.split(':').map(Number);
      const [endHour, endMin] = formData.end_time.split(':').map(Number);
      const startMinutes = startHour * 60 + startMin;
      const endMinutes = endHour * 60 + endMin;

      if (startMinutes >= endMinutes) {
        newErrors.end_time = 'End time must be after start time';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Ensure time format is HH:MM:SS
      const dataToSend = {
        subject_id: parseInt(formData.subject_id),
        day: formData.day,
        start_time: formData.start_time.includes(':') && formData.start_time.split(':').length === 2 
          ? `${formData.start_time}:00` 
          : formData.start_time,
        end_time: formData.end_time.includes(':') && formData.end_time.split(':').length === 2 
          ? `${formData.end_time}:00` 
          : formData.end_time,
        task_type: formData.task_type,
        notes: formData.notes || ''
      };
      
      console.log('📤 Sending session update:', dataToSend);
      
      await onSave(dataToSend);
      onClose();
    } catch (error) {
      console.error('❌ Session save error:', error);
      setErrors({
        submit: error.message || 'An error occurred during save'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!session?.id) return;

    if (window.confirm('Are you sure you want to delete this study session?')) {
      setIsSubmitting(true);
      try {
        await onDelete(session.id);
        onClose();
      } catch (error) {
        setErrors({
          submit: error.message || 'An error occurred during delete'
        });
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div 
          className="fixed inset-0 bg-slate-950/85 backdrop-blur-sm transition-opacity" 
          aria-hidden="true"
          onClick={onClose}
        ></div>

        {/* Center modal */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-slate-900 border border-white/10 rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            {/* Header */}
            <div className="bg-slate-950/40 px-6 py-4 border-b border-white/5">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white" id="modal-title">
                  {session ? 'Edit Session' : 'New Session'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-white/40 hover:text-white transition-colors"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-5 bg-slate-900">
              {/* Subject */}
              <div>
                <label htmlFor="subject_id" className="block text-sm font-semibold text-white/60 mb-1.5">
                  Subject *
                </label>
                <select
                  id="subject_id"
                  name="subject_id"
                  value={formData.subject_id}
                  onChange={handleChange}
                  className={`w-full px-3.5 py-2.5 bg-white/5 border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all ${
                    errors.subject_id ? 'border-red-500/50 focus:ring-red-500/30' : 'border-white/10'
                  }`}
                  required
                >
                  <option value="">Select a subject</option>
                  {Array.isArray(subjects) && subjects.map(subject => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
                {errors.subject_id && (
                  <p className="mt-1.5 text-xs text-red-400">{errors.subject_id}</p>
                )}
              </div>

              {/* Day of week */}
              <div>
                <label htmlFor="day_of_week" className="block text-sm font-semibold text-white/60 mb-1.5">
                  Day of the Week *
                </label>
                <select
                  id="day_of_week"
                  name="day_of_week"
                  value={formData.day_of_week}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
                  required
                >
                  {daysOfWeek.map(day => (
                    <option key={day} value={day}>{day}</option>
                  ))}
                </select>
              </div>

              {/* Time range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="start_time" className="block text-sm font-semibold text-white/60 mb-1.5">
                    Start Time *
                  </label>
                  <input
                    type="time"
                    id="start_time"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleChange}
                    className={`w-full px-3.5 py-2.5 bg-white/5 border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all ${
                      errors.start_time ? 'border-red-500/50 focus:ring-red-500/30' : 'border-white/10'
                    }`}
                    required
                  />
                  {errors.start_time && (
                    <p className="mt-1.5 text-xs text-red-400">{errors.start_time}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="end_time" className="block text-sm font-semibold text-white/60 mb-1.5">
                    End Time *
                  </label>
                  <input
                    type="time"
                    id="end_time"
                    name="end_time"
                    value={formData.end_time}
                    onChange={handleChange}
                    className={`w-full px-3.5 py-2.5 bg-white/5 border rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all ${
                      errors.end_time ? 'border-red-500/50 focus:ring-red-500/30' : 'border-white/10'
                    }`}
                    required
                  />
                  {errors.end_time && (
                    <p className="mt-1.5 text-xs text-red-400">{errors.end_time}</p>
                  )}
                </div>
              </div>

              {/* Task type */}
              <div>
                <label htmlFor="task_type" className="block text-sm font-semibold text-white/60 mb-1.5">
                  Task Type *
                </label>
                <select
                  id="task_type"
                  name="task_type"
                  value={formData.task_type}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
                  required
                >
                  {taskTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Notes */}
              <div>
                <label htmlFor="notes" className="block text-sm font-semibold text-white/60 mb-1.5">
                  Notes (optional)
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
                  placeholder="Add notes..."
                />
              </div>

              {/* Submit error */}
              {errors.submit && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                  <p className="text-sm text-red-400">{errors.submit}</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-slate-950/40 px-6 py-4 border-t border-white/5 flex items-center justify-between">
              <div>
                {session && (
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isSubmitting}
                    className="px-4 py-2 text-sm font-semibold text-red-400 hover:text-red-300 disabled:opacity-50 transition-colors"
                  >
                    Delete
                  </button>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="px-4 py-2 text-sm font-semibold text-white/70 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 disabled:opacity-50 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 text-sm font-bold text-white bg-gradient-to-r from-violet-600 to-indigo-500 rounded-xl shadow-glow-sm hover:shadow-glow-violet hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isSubmitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

SessionEditor.propTypes = {
  session: PropTypes.shape({
    id: PropTypes.number,
    subject_id: PropTypes.number,
    day_of_week: PropTypes.string,
    start_time: PropTypes.string,
    end_time: PropTypes.string,
    task_type: PropTypes.string,
    notes: PropTypes.string,
  }),
  subjects: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
    })
  ),
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
  onClose: PropTypes.func.isRequired,
  isOpen: PropTypes.bool.isRequired,
};

export default SessionEditor;
