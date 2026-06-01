import { useState, useEffect } from 'react';
import apiClient from '../api/client';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Input from './ui/Input';

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

const AvailabilityManager = () => {
  const [availabilities, setAvailabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAvailability, setEditingAvailability] = useState(null);
  const [formData, setFormData] = useState({
    day_of_week: 'Monday',
    start_time: '09:00',
    end_time: '17:00'
  });
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

  useEffect(() => {
    loadAvailabilities();
  }, []);

  const handleAdd = () => {
    setEditingAvailability(null);
    setFormData({
      day_of_week: 'Monday',
      start_time: '09:00',
      end_time: '17:00'
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleEdit = (availability) => {
    setEditingAvailability(availability);
    setFormData({
      day_of_week: availability.day_of_week,
      start_time: availability.start_time.substring(0, 5), // HH:MM
      end_time: availability.end_time.substring(0, 5)
    });
    setErrors({});
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette disponibilité ?')) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/availabilities/${id}`);
      setAvailabilities(prev => prev.filter(a => a.id !== id));
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate time range
    if (formData.start_time >= formData.end_time) {
      newErrors.end_time = 'L\'heure de fin doit être après l\'heure de début';
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
      const payload = {
        day_of_week: formData.day_of_week,
        start_time: formData.start_time + ':00', // Add seconds
        end_time: formData.end_time + ':00'
      };

      if (editingAvailability) {
        const response = await apiClient.put(`/api/v1/availabilities/${editingAvailability.id}`, payload);
        setAvailabilities(prev => prev.map(a => a.id === editingAvailability.id ? response.data : a));
      } else {
        const response = await apiClient.post('/api/v1/availabilities', payload);
        setAvailabilities(prev => [...prev, response.data]);
      }
      setIsModalOpen(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  // Group availabilities by day
  const groupedAvailabilities = DAYS_OF_WEEK.reduce((acc, day) => {
    acc[day] = availabilities.filter(a => a.day_of_week === day);
    return acc;
  }, {});

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Mes Disponibilités</h2>
          <p className="text-gray-600 mt-1">{availabilities.length} créneau(x) défini(s)</p>
        </div>
        <Button onClick={handleAdd}>
          + Ajouter une disponibilité
        </Button>
      </div>

      {availabilities.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune disponibilité</h3>
          <p className="mt-1 text-sm text-gray-500">Définissez vos créneaux horaires disponibles pour étudier.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {DAYS_OF_WEEK.map(day => (
            <div key={day} className="bg-white rounded-lg shadow border border-gray-200">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">{DAY_LABELS[day]}</h3>
              </div>
              <div className="p-4">
                {groupedAvailabilities[day].length === 0 ? (
                  <p className="text-gray-500 text-sm">Aucune disponibilité</p>
                ) : (
                  <div className="space-y-2">
                    {groupedAvailabilities[day].map(availability => (
                      <div key={availability.id} className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="font-medium text-gray-900">
                            {availability.start_time.substring(0, 5)} - {availability.end_time.substring(0, 5)}
                          </span>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(availability)}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDelete(availability.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
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
        title={editingAvailability ? 'Modifier la disponibilité' : 'Nouvelle disponibilité'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
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
              {editingAvailability ? 'Modifier' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AvailabilityManager;
