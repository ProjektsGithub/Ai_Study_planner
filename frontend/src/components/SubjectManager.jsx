import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

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
    exam_date: ''
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

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

  const handleAdd = () => {
    setEditingSubject(null);
    setFormData({
      name: '',
      priority: 3,
      difficulty: 3,
      target_weekly_hours: 3,
      exam_date: ''
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleEdit = (subject) => {
    setEditingSubject(subject);
    setFormData({
      name: subject.name,
      priority: subject.priority,
      difficulty: subject.difficulty,
      target_weekly_hours: subject.target_weekly_hours,
      exam_date: subject.exam_date || ''
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette matière ?')) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/subjects/${id}`);
      setSubjects(prev => prev.filter(s => s.id !== id));
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['priority', 'difficulty', 'target_weekly_hours'].includes(name)
        ? parseFloat(value)
        : value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name || formData.name.length < 1 || formData.name.length > 100) {
      newErrors.name = 'Le nom doit contenir entre 1 et 100 caractères';
    }

    if (formData.priority < 1 || formData.priority > 5) {
      newErrors.priority = 'La priorité doit être entre 1 et 5';
    }

    if (formData.difficulty < 1 || formData.difficulty > 5) {
      newErrors.difficulty = 'La difficulté doit être entre 1 et 5';
    }

    if (formData.target_weekly_hours < 0.5 || formData.target_weekly_hours > 168) {
      newErrors.target_weekly_hours = 'Les heures doivent être entre 0.5 et 168';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSaving(true);

    try {
      if (editingSubject) {
        const response = await apiClient.put(`/api/v1/subjects/${editingSubject.id}`, formData);
        setSubjects(prev => prev.map(s => s.id === editingSubject.id ? response.data : s));
      } else {
        const response = await apiClient.post('/api/v1/subjects', formData);
        setSubjects(prev => [...prev, response.data]);
      }
      setIsModalOpen(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Mes Matières</h2>
          <p className="text-gray-600 mt-1">{subjects.length} matière(s)</p>
        </div>
        <Button onClick={handleAdd} disabled={subjects.length >= 100}>
          + Ajouter une matière
        </Button>
      </div>

      {subjects.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune matière</h3>
          <p className="mt-1 text-sm text-gray-500">Commencez par ajouter vos matières.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subjects.map(subject => (
            <div key={subject.id} className="bg-white rounded-lg shadow p-4 border border-gray-200">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{subject.name}</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(subject)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(subject.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Priorité:</span>
                  <span className="font-medium">{'⭐'.repeat(subject.priority)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Difficulté:</span>
                  <span className="font-medium">{'📊'.repeat(subject.difficulty)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Heures/semaine:</span>
                  <span className="font-medium">{subject.target_weekly_hours}h</span>
                </div>
                {subject.exam_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Examen:</span>
                    <span className="font-medium">{new Date(subject.exam_date).toLocaleDateString('fr-FR')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSubject ? 'Modifier la matière' : 'Nouvelle matière'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nom de la matière *"
            name="name"
            value={formData.name}
            onChange={handleChange}
            error={errors.name}
            required
            maxLength={100}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Priorité (1-5) *"
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
              label="Difficulté (1-5) *"
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
            label="Heures cibles/semaine *"
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

          <Input
            label="Date d'examen (optionnel)"
            type="date"
            name="exam_date"
            value={formData.exam_date}
            onChange={handleChange}
            error={errors.exam_date}
          />

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
              disabled={saving}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={saving}
              disabled={saving}
            >
              {editingSubject ? 'Modifier' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default SubjectManager;
