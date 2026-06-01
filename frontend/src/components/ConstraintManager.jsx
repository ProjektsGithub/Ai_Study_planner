import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

const CONSTRAINT_TYPES = {
  forbidden_slot: 'Créneau interdit',
  max_daily_hours: 'Heures max par jour',
  required_break: 'Pause obligatoire',
  fixed_slot: 'Créneau fixe'
};

const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
];

const DAY_LABELS = {
  'Monday': 'Lundi',
  'Tuesday': 'Mardi',
  'Wednesday': 'Mercredi',
  'Thursday': 'Jeudi',
  'Friday': 'Vendredi',
  'Saturday': 'Samedi',
  'Sunday': 'Dimanche'
};

const ConstraintManager = () => {
  const [constraints, setConstraints] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConstraint, setEditingConstraint] = useState(null);
  const [formData, setFormData] = useState({
    constraint_type: 'forbidden_slot',
    active: true,
    // forbidden_slot / fixed_slot
    day_of_week: 'Monday',
    start_time: '12:00',
    end_time: '13:00',
    // fixed_slot
    subject_id: '',
    // max_daily_hours
    max_hours: 8,
    // required_break
    duration_minutes: 15,
    after_minutes: 120
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const loadConstraints = async () => {
    try {
      const response = await apiClient.get('/api/v1/constraints');
      setConstraints(response.data.constraints || []);
    } catch (error) {
      console.error('Error loading constraints:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSubjects = async () => {
    try {
      const response = await apiClient.get('/api/v1/subjects');
      setSubjects(response.data || []);
    } catch (error) {
      console.error('Error loading subjects:', error);
    }
  };

  useEffect(() => {
    loadConstraints();
    loadSubjects();
  }, []);

  const handleAdd = () => {
    setEditingConstraint(null);
    setFormData({
      constraint_type: 'forbidden_slot',
      active: true,
      day_of_week: 'Monday',
      start_time: '12:00',
      end_time: '13:00',
      subject_id: '',
      max_hours: 8,
      duration_minutes: 15,
      after_minutes: 120
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleEdit = (constraint) => {
    setEditingConstraint(constraint);
    const params = constraint.parameters;
    
    setFormData({
      constraint_type: constraint.constraint_type,
      active: constraint.active,
      day_of_week: params.day_of_week || 'Monday',
      start_time: params.start_time ? params.start_time.substring(0, 5) : '12:00',
      end_time: params.end_time ? params.end_time.substring(0, 5) : '13:00',
      subject_id: params.subject_id || '',
      max_hours: params.max_hours || 8,
      duration_minutes: params.duration_minutes || 15,
      after_minutes: params.after_minutes || 120
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette contrainte ?')) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/constraints/${id}`);
      setConstraints(prev => prev.filter(c => c.id !== id));
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : 
              ['max_hours', 'duration_minutes', 'after_minutes', 'subject_id'].includes(name) ? 
              (value === '' ? '' : parseFloat(value)) : value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const type = formData.constraint_type;

    if (type === 'forbidden_slot' || type === 'fixed_slot') {
      if (formData.start_time >= formData.end_time) {
        newErrors.end_time = 'L\'heure de fin doit être après l\'heure de début';
      }
      
      if (type === 'fixed_slot' && !formData.subject_id) {
        newErrors.subject_id = 'Veuillez sélectionner une matière';
      }
    }

    if (type === 'max_daily_hours') {
      if (formData.max_hours < 1 || formData.max_hours > 24) {
        newErrors.max_hours = 'Les heures doivent être entre 1 et 24';
      }
    }

    if (type === 'required_break') {
      if (formData.duration_minutes < 5 || formData.duration_minutes > 120) {
        newErrors.duration_minutes = 'La durée doit être entre 5 et 120 minutes';
      }
      if (formData.after_minutes < 30 || formData.after_minutes > 240) {
        newErrors.after_minutes = 'La fréquence doit être entre 30 et 240 minutes';
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

    setSaving(true);

    try {
      let parameters = {};
      
      switch (formData.constraint_type) {
        case 'forbidden_slot': {
          parameters = {
            day_of_week: formData.day_of_week,
            start_time: formData.start_time + ':00',
            end_time: formData.end_time + ':00'
          };
          break;
        }
        case 'max_daily_hours': {
          parameters = {
            max_hours: formData.max_hours
          };
          break;
        }
        case 'required_break': {
          parameters = {
            duration_minutes: formData.duration_minutes,
            after_minutes: formData.after_minutes
          };
          break;
        }
        case 'fixed_slot': {
          parameters = {
            day_of_week: formData.day_of_week,
            start_time: formData.start_time + ':00',
            end_time: formData.end_time + ':00',
            subject_id: formData.subject_id
          };
          break;
        }
      }

      const payload = {
        constraint_type: formData.constraint_type,
        parameters,
        active: formData.active
      };

      if (editingConstraint) {
        const response = await apiClient.put(`/api/v1/constraints/${editingConstraint.id}`, payload);
        setConstraints(prev => prev.map(c => c.id === editingConstraint.id ? response.data : c));
      } else {
        const response = await apiClient.post('/api/v1/constraints', payload);
        setConstraints(prev => [...prev, response.data]);
      }
      setIsModalOpen(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (constraint) => {
    try {
      const response = await apiClient.put(`/api/v1/constraints/${constraint.id}`, {
        active: !constraint.active
      });
      setConstraints(prev => prev.map(c => c.id === constraint.id ? response.data : c));
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la mise à jour');
    }
  };

  const getConstraintDescription = (constraint) => {
    const params = constraint.parameters;
    
    switch (constraint.constraint_type) {
      case 'forbidden_slot':
        return `${DAY_LABELS[params.day_of_week]} ${params.start_time.substring(0, 5)} - ${params.end_time.substring(0, 5)}`;
      case 'max_daily_hours':
        return `Maximum ${params.max_hours}h par jour`;
      case 'required_break':
        return `Pause de ${params.duration_minutes}min toutes les ${params.after_minutes}min`;
      case 'fixed_slot': {
        const subject = subjects.find(s => s.id === params.subject_id);
        return `${DAY_LABELS[params.day_of_week]} ${params.start_time.substring(0, 5)} - ${params.end_time.substring(0, 5)} (${subject?.name || 'Matière inconnue'})`;
      }
      default:
        return 'Contrainte inconnue';
    }
  };

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Mes Contraintes</h2>
          <p className="text-gray-600 mt-1">
            {constraints.length} contrainte(s) - {constraints.filter(c => c.active).length} active(s)
          </p>
        </div>
        <Button onClick={handleAdd}>
          + Ajouter une contrainte
        </Button>
      </div>

      {constraints.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune contrainte</h3>
          <p className="mt-1 text-sm text-gray-500">Ajoutez des contraintes pour personnaliser votre planning.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {constraints.map(constraint => (
            <div
              key={constraint.id}
              className={`bg-white rounded-lg shadow border p-4 ${
                constraint.active ? 'border-gray-200' : 'border-gray-300 opacity-60'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      constraint.constraint_type === 'forbidden_slot' ? 'bg-red-100 text-red-800' :
                      constraint.constraint_type === 'max_daily_hours' ? 'bg-yellow-100 text-yellow-800' :
                      constraint.constraint_type === 'required_break' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {CONSTRAINT_TYPES[constraint.constraint_type]}
                    </span>
                    {!constraint.active && (
                      <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                        Désactivée
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-gray-900 font-medium">
                    {getConstraintDescription(constraint)}
                  </p>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => toggleActive(constraint)}
                    className={`p-2 rounded ${
                      constraint.active 
                        ? 'text-green-600 hover:bg-green-50' 
                        : 'text-gray-400 hover:bg-gray-50'
                    }`}
                    title={constraint.active ? 'Désactiver' : 'Activer'}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleEdit(constraint)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(constraint.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingConstraint ? 'Modifier la contrainte' : 'Nouvelle contrainte'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type de contrainte *
            </label>
            <select
              name="constraint_type"
              value={formData.constraint_type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={!!editingConstraint}
            >
              {Object.entries(CONSTRAINT_TYPES).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {(formData.constraint_type === 'forbidden_slot' || formData.constraint_type === 'fixed_slot') && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jour de la semaine *
                </label>
                <select
                  name="day_of_week"
                  value={formData.day_of_week}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {DAYS_OF_WEEK.map(day => (
                    <option key={day} value={day}>{DAY_LABELS[day]}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Heure de début *"
                  type="time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleChange}
                  error={errors.start_time}
                  required
                />

                <Input
                  label="Heure de fin *"
                  type="time"
                  name="end_time"
                  value={formData.end_time}
                  onChange={handleChange}
                  error={errors.end_time}
                  required
                />
              </div>

              {formData.constraint_type === 'fixed_slot' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Matière *
                  </label>
                  <select
                    name="subject_id"
                    value={formData.subject_id}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Sélectionner une matière</option>
                    {subjects.map(subject => (
                      <option key={subject.id} value={subject.id}>{subject.name}</option>
                    ))}
                  </select>
                  {errors.subject_id && (
                    <p className="mt-1 text-sm text-red-600">{errors.subject_id}</p>
                  )}
                </div>
              )}
            </>
          )}

          {formData.constraint_type === 'max_daily_hours' && (
            <Input
              label="Heures maximum par jour *"
              type="number"
              name="max_hours"
              value={formData.max_hours}
              onChange={handleChange}
              min="1"
              max="24"
              step="0.5"
              error={errors.max_hours}
              required
            />
          )}

          {formData.constraint_type === 'required_break' && (
            <>
              <Input
                label="Durée de la pause (minutes) *"
                type="number"
                name="duration_minutes"
                value={formData.duration_minutes}
                onChange={handleChange}
                min="5"
                max="120"
                error={errors.duration_minutes}
                required
              />

              <Input
                label="Après combien de minutes (fréquence) *"
                type="number"
                name="after_minutes"
                value={formData.after_minutes}
                onChange={handleChange}
                min="30"
                max="240"
                error={errors.after_minutes}
                required
              />
            </>
          )}

          <div className="flex items-center">
            <input
              type="checkbox"
              name="active"
              checked={formData.active}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              Contrainte active
            </label>
          </div>

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
              {editingConstraint ? 'Modifier' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ConstraintManager;
