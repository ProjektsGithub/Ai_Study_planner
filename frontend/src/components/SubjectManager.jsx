import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

/* ── Star rating display ── */
const StarBar = ({ value, max = 5, color = 'violet' }) => {
  const colors = {
    violet: 'bg-violet-500',
    amber: 'bg-amber-500',
    cyan: 'bg-cyan-500',
  };
  return (
    <div className="flex gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-all ${i < value ? colors[color] : 'bg-white/10'}`}
        />
      ))}
    </div>
  );
};

const SubjectManager = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
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
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadSubjects(); }, []);

  const loadSubjects = async () => {
    try {
      const response = await apiClient.get('/api/v1/subjects');
      setSubjects(response.data?.subjects || []);
    } catch (error) {
      console.error('Error loading subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const defaultForm = {
    name: '', priority: 3, difficulty: 3, target_weekly_hours: 3,
    exam_date: '', exam_type: '', ects_credits: '', coefficient: '',
    is_mandatory: true, validation_status: 'in_progress',
    weekly_class_hours: '', current_progress: 0, weak_topics: [],
  };

  const handleAdd = () => {
    setEditingSubject(null);
    setFormData(defaultForm);
    setErrors({});
    setIsModalOpen(true);
  };

  const handleEdit = (subject) => {
    console.log('📝 Editing subject:', subject);
    console.log('📝 validation_status from DB:', subject.validation_status);
    
    setEditingSubject(subject);
    setFormData({
      name: subject.name,
      priority: subject.priority,
      difficulty: subject.difficulty,
      target_weekly_hours: subject.target_weekly_hours,
      exam_date: subject.exam_date || '',
      exam_type: subject.exam_type || '',
      ects_credits: subject.ects_credits || '',
      coefficient: subject.coefficient || '',
      is_mandatory: subject.is_mandatory !== undefined ? subject.is_mandatory : true,
      validation_status: subject.validation_status || 'in_progress',
      weekly_class_hours: subject.weekly_class_hours || '',
      current_progress: subject.current_progress || 0,
      weak_topics: subject.weak_topics || [],
    });
    
    console.log('📝 Form data set to:', {
      name: subject.name,
      validation_status: subject.validation_status || 'in_progress'
    });
    
    setErrors({});
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Supprimer cette matière ?')) return;
    try {
      await apiClient.delete(`/api/v1/subjects/${id}`);
      setSubjects((prev) => prev.filter((s) => s.id !== id));
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

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
    const topic = prompt('Entrer un point faible :');
    if (topic?.trim()) {
      setFormData((prev) => ({ ...prev, weak_topics: [...prev.weak_topics, topic.trim()] }));
    }
  };

  const handleRemoveWeakTopic = (index) => {
    setFormData((prev) => ({ ...prev, weak_topics: prev.weak_topics.filter((_, i) => i !== index) }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name || formData.name.length < 1) newErrors.name = 'Nom requis';
    if (formData.priority < 1 || formData.priority > 5) newErrors.priority = 'Entre 1 et 5';
    if (formData.difficulty < 1 || formData.difficulty > 5) newErrors.difficulty = 'Entre 1 et 5';
    if (formData.target_weekly_hours < 0.5) newErrors.target_weekly_hours = 'Min 0.5h';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSaving(true);
    try {
      const cleanedData = { ...formData };
      ['ects_credits', 'coefficient', 'exam_type', 'exam_date', 'weekly_class_hours', 'weak_topics'].forEach((f) => {
        if (cleanedData[f] === '' || (Array.isArray(cleanedData[f]) && cleanedData[f].length === 0)) {
          cleanedData[f] = null;
        }
      });
      if (editingSubject) {
        const res = await apiClient.put(`/api/v1/subjects/${editingSubject.id}`, cleanedData);
        setSubjects((prev) => prev.map((s) => s.id === editingSubject.id ? res.data : s));
      } else {
        const res = await apiClient.post('/api/v1/subjects', cleanedData);
        setSubjects((prev) => [...prev, res.data]);
      }
      setIsModalOpen(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const statusColors = {
    in_progress: 'badge-violet',
    validated: 'badge-success',
    not_started: 'badge-cyan',
    failed: 'bg-red-500/15 text-red-400 border border-red-500/25',
  };
  const statusLabels = {
    in_progress: 'En cours',
    validated: 'Validé',
    not_started: 'Non commencé',
    failed: 'À repasser',
  };

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
          <h2 className="text-2xl font-bold text-white">Mes Matières</h2>
          <p className="text-white/40 text-sm mt-1">{subjects.length} matière(s) enregistrée(s)</p>
        </div>
        <Button onClick={handleAdd} disabled={subjects.length >= 100} size="md">
          + Ajouter une matière
        </Button>
      </div>

      {/* Empty */}
      {subjects.length === 0 ? (
        <div className="empty-state">
          <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h3 className="text-white/60 font-medium mb-1">Aucune matière</h3>
          <p className="text-white/30 text-sm">Commencez par ajouter vos matières.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subjects.map((subject) => (
            <div
              key={subject.id}
              className="relative rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-md p-5 hover:border-violet-500/30 hover:-translate-y-1 transition-all duration-300"
            >
              {/* Top bar */}
              <div className="absolute top-0 left-5 right-5 h-0.5 rounded-b-full bg-gradient-to-r from-violet-500 to-indigo-500 opacity-50" />

              <div className="flex justify-between items-start mb-4">
                <h3 className="text-base font-semibold text-white pr-2 leading-snug">{subject.name}</h3>
                <div className="flex gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => handleEdit(subject)}
                    className="p-1.5 rounded-lg text-white/30 hover:text-violet-400 hover:bg-violet-500/10 transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(subject.id)}
                    className="p-1.5 rounded-lg text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="space-y-3 text-sm">
                <div>
                  <div className="flex justify-between text-xs text-white/40 mb-1">
                    <span>Priorité</span>
                    <span>{subject.priority}/5</span>
                  </div>
                  <StarBar value={subject.priority} color="violet" />
                </div>
                <div>
                  <div className="flex justify-between text-xs text-white/40 mb-1">
                    <span>Difficulté</span>
                    <span>{subject.difficulty}/5</span>
                  </div>
                  <StarBar value={subject.difficulty} color="amber" />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <span className="text-white/40 text-xs">{subject.target_weekly_hours}h / semaine</span>
                  <span className={`badge text-xs ${statusColors[subject.validation_status] || 'badge-violet'}`}>
                    {statusLabels[subject.validation_status] || subject.validation_status}
                  </span>
                </div>

                {subject.exam_date && (
                  <div className="flex items-center gap-2 text-xs text-cyan-400/70">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Examen : {new Date(subject.exam_date).toLocaleDateString('fr-FR')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSubject ? 'Modifier la matière' : 'Nouvelle matière'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Nom de la matière *"
            name="name"
            value={formData.name}
            onChange={handleChange}
            error={errors.name}
            required
            maxLength={100}
            placeholder="Ex: Mathématiques, Physique..."
          />

          <div className="grid grid-cols-2 gap-4">
            <Input label="Crédits ECTS" type="number" name="ects_credits" value={formData.ects_credits} onChange={handleChange} min="0" max="30" step="0.5" placeholder="Ex: 6" />
            <Input label="Coefficient" type="number" name="coefficient" value={formData.coefficient} onChange={handleChange} min="0" max="10" step="0.5" placeholder="Ex: 2" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">Type d'examen</label>
              <select 
                name="exam_type" 
                value={formData.exam_type} 
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all"
              >
                <option value="">Sélectionner</option>
                <option value="written_exam">Écrit</option>
                <option value="oral">Oral</option>
                <option value="project">Projet</option>
                <option value="continuous_assessment">Contrôle continu</option>
                <option value="mixed">Mixte</option>
              </select>
            </div>
            <Input label="Date d'examen" type="date" name="exam_date" value={formData.exam_date} onChange={handleChange} error={errors.exam_date} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">Statut</label>
              <select 
                name="validation_status" 
                value={formData.validation_status} 
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all"
              >
                <option value="not_started">Non commencé</option>
                <option value="in_progress">En cours</option>
                <option value="validated">Validé</option>
                <option value="failed">À repasser</option>
              </select>
            </div>
            <Input label="Heures de cours/semaine" type="number" name="weekly_class_hours" value={formData.weekly_class_hours} onChange={handleChange} min="0" max="168" step="0.5" placeholder="CM + TD + TP" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input label="Priorité (1-5) *" type="number" name="priority" value={formData.priority} onChange={handleChange} min="1" max="5" error={errors.priority} required />
            <Input label="Difficulté (1-5) *" type="number" name="difficulty" value={formData.difficulty} onChange={handleChange} min="1" max="5" error={errors.difficulty} required />
          </div>

          <Input label="Objectif heures/semaine *" type="number" name="target_weekly_hours" value={formData.target_weekly_hours} onChange={handleChange} min="0.5" max="168" step="0.5" error={errors.target_weekly_hours} required />

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">
              Progression actuelle : <span className="text-violet-400 font-bold">{formData.current_progress}%</span>
            </label>
            <input
              type="range"
              name="current_progress"
              value={formData.current_progress}
              onChange={handleChange}
              min="0" max="100" step="5"
            />
          </div>

          <label className="flex items-center gap-3 cursor-pointer group">
            <input type="checkbox" name="is_mandatory" checked={formData.is_mandatory} onChange={handleChange} />
            <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">Matière obligatoire</span>
          </label>

          {/* Weak topics */}
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Points faibles</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {formData.weak_topics.map((topic, index) => (
                <span key={index} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-red-500/15 text-red-300 border border-red-500/25">
                  {topic}
                  <button type="button" onClick={() => handleRemoveWeakTopic(index)} className="text-red-400 hover:text-red-200 transition-colors">×</button>
                </span>
              ))}
            </div>
            <Button type="button" variant="outline" size="sm" onClick={handleAddWeakTopic}>
              + Ajouter un point faible
            </Button>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)} disabled={saving}>Annuler</Button>
            <Button type="submit" variant="primary" loading={saving} disabled={saving}>
              {editingSubject ? 'Mettre à jour' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default SubjectManager;
