import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Button from '../ui/Button';
import Input from '../ui/Input';

const SubjectForm = ({ initialData, onSubmit, onCancel, saving }) => {
  const [formData, setFormData] = useState({
    name: '',
    priority: 3,
    difficulty: 3,
    target_weekly_hours: 3,
    exam_date: '',
    exam_type: '',
    ects_credits: '',
    coefficient: '',
    is_mandatory: true,
    validation_status: 'in_progress',
    weekly_class_hours: '',
    current_progress: 0,
    weak_topics: [],
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        priority: initialData.priority || 3,
        difficulty: initialData.difficulty || 3,
        target_weekly_hours: initialData.target_weekly_hours || 3,
        exam_date: initialData.exam_date || '',
        exam_type: initialData.exam_type || '',
        ects_credits: initialData.ects_credits || '',
        coefficient: initialData.coefficient || '',
        is_mandatory: initialData.is_mandatory !== undefined ? initialData.is_mandatory : true,
        validation_status: initialData.validation_status || 'in_progress',
        weekly_class_hours: initialData.weekly_class_hours || '',
        current_progress: initialData.current_progress || 0,
        weak_topics: initialData.weak_topics || [],
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const numericFields = ['priority', 'difficulty', 'target_weekly_hours', 'ects_credits', 'coefficient', 'weekly_class_hours', 'current_progress'];
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (numericFields.includes(name) ? (value === '' ? '' : parseFloat(value)) : value),
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const handleAddWeakTopic = () => {
    const topic = prompt('Add a weak area / difficult chapter:');
    if (topic?.trim()) {
      setFormData((prev) => ({ ...prev, weak_topics: [...prev.weak_topics, topic.trim()] }));
    }
  };

  const handleRemoveWeakTopic = (index) => {
    setFormData((prev) => ({ ...prev, weak_topics: prev.weak_topics.filter((_, i) => i !== index) }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Subject name is required';
    if (formData.priority < 1 || formData.priority > 5) newErrors.priority = 'Priority must be between 1 and 5';
    if (formData.difficulty < 1 || formData.difficulty > 5) newErrors.difficulty = 'Difficulty must be between 1 and 5';
    if (formData.target_weekly_hours < 0.5) newErrors.target_weekly_hours = 'Minimum revision goal is 0.5 hours';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    const cleaned = { ...formData };
    ['ects_credits', 'coefficient', 'exam_type', 'exam_date', 'weekly_class_hours'].forEach((field) => {
      if (cleaned[field] === '') cleaned[field] = null;
    });

    onSubmit(cleaned);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Input
        label="Subject Name *"
        name="name"
        value={formData.name}
        onChange={handleChange}
        error={errors.name}
        required
        maxLength={100}
        placeholder="e.g. Programming, Physics..."
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="ECTS Credits"
          type="number"
          name="ects_credits"
          value={formData.ects_credits}
          onChange={handleChange}
          min="0"
          max="30"
          step="0.5"
          placeholder="e.g. 6"
        />
        <Input
          label="Coefficient / Exam Weight"
          type="number"
          name="coefficient"
          value={formData.coefficient}
          onChange={handleChange}
          min="0"
          max="10"
          step="0.1"
          placeholder="e.g. 1.5"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Exam Type</label>
          <select name="exam_type" value={formData.exam_type} onChange={handleChange}>
            <option value="">Select</option>
            <option value="written_exam">Written</option>
            <option value="oral">Oral</option>
            <option value="project">Project</option>
            <option value="continuous_assessment">Continuous Assessment</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>
        <Input
          label="Exam Date"
          type="date"
          name="exam_date"
          value={formData.exam_date}
          onChange={handleChange}
          error={errors.exam_date}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Validation Status</label>
          <select name="validation_status" value={formData.validation_status} onChange={handleChange}>
            <option value="not_started">Not Started</option>
            <option value="in_progress">In Progress</option>
            <option value="validated">Validated</option>
            <option value="failed">Failed / Retake</option>
          </select>
        </div>
        <Input
          label="Class Hours / Week"
          type="number"
          name="weekly_class_hours"
          value={formData.weekly_class_hours}
          onChange={handleChange}
          min="0"
          max="168"
          step="0.5"
          placeholder="e.g. 4"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Priority (1-5) *"
          type="number"
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          min="1"
          max="5"
          error={errors.priority}
          required
        />
        <Input
          label="Difficulty (1-5) *"
          type="number"
          name="difficulty"
          value={formData.difficulty}
          onChange={handleChange}
          min="1"
          max="5"
          error={errors.difficulty}
          required
        />
      </div>

      <Input
        label="Weekly Revision Goal (hours) *"
        type="number"
        name="target_weekly_hours"
        value={formData.target_weekly_hours}
        onChange={handleChange}
        min="0.5"
        max="168"
        step="0.5"
        error={errors.target_weekly_hours}
        required
      />

      <div>
        <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
          Course Progression: <span className="text-violet-400 font-bold">{formData.current_progress}%</span>
        </label>
        <input
          type="range"
          name="current_progress"
          value={formData.current_progress}
          onChange={handleChange}
          min="0"
          max="100"
          step="5"
        />
      </div>

      <label className="flex items-center gap-3 cursor-pointer group">
        <input type="checkbox" name="is_mandatory" checked={formData.is_mandatory} onChange={handleChange} />
        <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">Mandatory Subject</span>
      </label>

      {/* Weak topics */}
      <div>
        <label className="block text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Difficult Chapters / Topics</label>
        <div className="flex flex-wrap gap-2 mb-3">
          {formData.weak_topics.map((topic, index) => (
            <span key={index} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] bg-red-500/10 text-red-300 border border-red-500/15">
              {topic}
              <button type="button" onClick={() => handleRemoveWeakTopic(index)} className="text-red-400 hover:text-red-200 transition-colors font-bold">×</button>
            </span>
          ))}
        </div>
        <Button type="button" variant="outline" size="sm" onClick={handleAddWeakTopic}>
          + Add a Topic
        </Button>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>Cancel</Button>
        <Button type="submit" variant="primary" loading={saving} disabled={saving}>
          {initialData ? 'Update Subject' : 'Add Subject'}
        </Button>
      </div>
    </form>
  );
};

SubjectForm.propTypes = {
  initialData: PropTypes.object,
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  saving: PropTypes.bool,
};

export default SubjectForm;
