import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useLanguage } from '../../context/LanguageContext';
import Button from '../ui/Button';
import Input from '../ui/Input';

const ExamForm = ({ initialData, subjects = [], onSubmit, onCancel, saving }) => {
  const { t } = useLanguage();

  const [formData, setFormData] = useState({
    course_id: '',
    course_name: '',
    exam_date: '',
    exam_time: '08:00',
    location: '',
    duration_minutes: 120,
    weight: 0.5,
    exam_type: 'final',
    notes: '',
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        course_id: initialData.course_id || '',
        course_name: initialData.course_name || '',
        exam_date: initialData.exam_date || '',
        exam_time: initialData.exam_time ? initialData.exam_time.slice(0, 5) : '08:00',
        location: initialData.location || '',
        duration_minutes: initialData.duration_minutes || 120,
        weight: initialData.weight || 0.5,
        exam_type: initialData.exam_type || 'final',
        notes: initialData.notes || '',
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numericFields = ['course_id', 'duration_minutes', 'weight'];
    
    setFormData((prev) => {
      const updated = {
        ...prev,
        [name]: numericFields.includes(name) ? (value === '' ? '' : parseFloat(value)) : value,
      };

      // Auto populate course name if subject is changed
      if (name === 'course_id') {
        const selectedSub = subjects.find((s) => s.id === parseInt(value, 10));
        updated.course_name = selectedSub ? selectedSub.name : '';
      }

      return updated;
    });

    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.course_id) newErrors.course_id = t('session_editor.error_subject_required');
    if (!formData.exam_date) newErrors.exam_date = 'Date requise';
    
    // Validate future date
    if (formData.exam_date) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const selected = new Date(formData.exam_date);
      if (selected < today) {
        newErrors.exam_date = "La date d'examen ne peut pas être passée";
      }
    }

    if (formData.weight < 0.0 || formData.weight > 1.0) {
      newErrors.weight = 'Le coefficient doit être compris entre 0.0 et 1.0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-xs font-semibold text-slate-500 dark:text-white/50 uppercase tracking-wider mb-2">{t('exams.form_subject')}</label>
        <select
          name="course_id"
          value={formData.course_id}
          onChange={handleChange}
          required
          className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-white/10 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-violet-500"
        >
          <option value="">{t('exams.form_select_subject')}</option>
          {subjects.map((sub) => (
            <option key={sub.id} value={sub.id}>{sub.name}</option>
          ))}
        </select>
        {errors.course_id && <p className="text-red-400 text-xs mt-1">{errors.course_id}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label={t('exams.form_date')}
          type="date"
          name="exam_date"
          value={formData.exam_date}
          onChange={handleChange}
          error={errors.exam_date}
          required
        />
        <Input
          label={t('exams.form_time')}
          type="time"
          name="exam_time"
          value={formData.exam_time}
          onChange={handleChange}
          required
        />
      </div>

      <Input
        label={t('exams.form_location')}
        name="location"
        value={formData.location}
        onChange={handleChange}
        placeholder={t('exams.form_location_placeholder')}
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          label={t('exams.form_duration')}
          type="number"
          name="duration_minutes"
          value={formData.duration_minutes}
          onChange={handleChange}
          min="1"
          max="600"
          required
        />
        <Input
          label={t('exams.form_weight')}
          type="number"
          name="weight"
          value={formData.weight}
          onChange={handleChange}
          min="0"
          max="1"
          step="0.05"
          error={errors.weight}
          required
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-slate-500 dark:text-white/50 uppercase tracking-wider mb-2">{t('exams.form_type')}</label>
        <select
          name="exam_type"
          value={formData.exam_type}
          onChange={handleChange}
          className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-white/10 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-violet-500"
        >
          <option value="midterm">{t('exams.type_midterm')}</option>
          <option value="final">{t('exams.type_final')}</option>
          <option value="practical">{t('exams.type_practical')}</option>
          <option value="oral">{t('exams.type_oral')}</option>
          <option value="project">{t('exams.type_project')}</option>
        </select>
      </div>

      <Input
        label={t('exams.form_notes')}
        name="notes"
        value={formData.notes}
        onChange={handleChange}
        placeholder={t('exams.form_notes_placeholder')}
      />

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-white/5">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>{t('action.cancel')}</Button>
        <Button type="submit" variant="primary" loading={saving} disabled={saving}>
          {initialData ? t('exams.form_update') : t('exams.modal_add_title')}
        </Button>
      </div>
    </form>
  );
};

ExamForm.propTypes = {
  initialData: PropTypes.object,
  subjects: PropTypes.array.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  saving: PropTypes.bool,
};

export default ExamForm;
