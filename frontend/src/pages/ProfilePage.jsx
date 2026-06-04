import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const ProfilePage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  
  const [formData, setFormData] = useState({
    cursus: '',
    academic_level: '',
    weekly_study_goal: 20,
    semester_start_date: '',
    semester_end_date: '',
    exam_period_start: '',
    total_course_hours_per_week: '',
    other_commitments_hours: '',
    preferred_study_time: '',
    preferred_session_duration: '',
    study_pace: '',
    preferences: {}
  });
  
  const [errors, setErrors] = useState({});

  const cursusOptions = [
    'Computer Science',
    'Mathematics',
    'Physics',
    'Engineering',
    'Business',
    'Medicine',
    'Law',
    'Other'
  ];

  const academicLevelOptions = [
    'Bachelor',
    'Master',
    'PhD',
    'Other'
  ];

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await apiClient.get('/api/v1/profile');
      if (response.data) {
        setFormData({
          cursus: response.data.cursus || '',
          academic_level: response.data.academic_level || '',
          weekly_study_goal: response.data.weekly_study_goal || 20,
          semester_start_date: response.data.semester_start_date || '',
          semester_end_date: response.data.semester_end_date || '',
          exam_period_start: response.data.exam_period_start || '',
          total_course_hours_per_week: response.data.total_course_hours_per_week || '',
          other_commitments_hours: response.data.other_commitments_hours || '',
          preferred_study_time: response.data.preferred_study_time || '',
          preferred_session_duration: response.data.preferred_session_duration || '',
          study_pace: response.data.study_pace || '',
          preferences: response.data.preferences || {}
        });
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numericFields = ['weekly_study_goal', 'total_course_hours_per_week', 'other_commitments_hours', 'preferred_session_duration'];
    
    setFormData(prev => ({
      ...prev,
      [name]: numericFields.includes(name) ? (value === '' ? '' : parseFloat(value)) : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.cursus) {
      newErrors.cursus = 'Cursus requis';
    }

    if (!formData.academic_level) {
      newErrors.academic_level = 'Niveau académique requis';
    }

    if (!formData.weekly_study_goal) {
      newErrors.weekly_study_goal = 'Objectif hebdomadaire requis';
    } else if (formData.weekly_study_goal < 1 || formData.weekly_study_goal > 168) {
      newErrors.weekly_study_goal = 'L\'objectif doit être entre 1 et 168 heures';
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
    setMessage(null);

    try {
      const cleanedData = { ...formData };
      
      // Convert empty strings to null for optional fields
      const optionalFields = [
        'semester_start_date', 'semester_end_date', 'exam_period_start',
        'total_course_hours_per_week', 'other_commitments_hours',
        'preferred_study_time', 'preferred_session_duration', 'study_pace'
      ];
      
      optionalFields.forEach(field => {
        if (cleanedData[field] === '') {
          cleanedData[field] = null;
        }
      });

      await apiClient.post('/api/v1/profile', cleanedData);
      setMessage({ type: 'success', text: 'Profil enregistré avec succès !' });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Erreur lors de la sauvegarde'
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Mon Profil</h1>
        <p className="mt-2 text-gray-600">
          Configurez votre profil étudiant pour personnaliser vos plans d'étude
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* User info */}
          <div className="pb-6 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Informations utilisateur
            </h3>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="text"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Academic info */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Informations académiques
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="cursus" className="block text-sm font-medium text-gray-700 mb-1">
                  Cursus *
                </label>
                <select
                  id="cursus"
                  name="cursus"
                  value={formData.cursus}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.cursus ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                >
                  <option value="">Sélectionner un cursus</option>
                  {cursusOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                {errors.cursus && (
                  <p className="mt-1 text-sm text-red-600">{errors.cursus}</p>
                )}
              </div>

              <div>
                <label htmlFor="academic_level" className="block text-sm font-medium text-gray-700 mb-1">
                  Niveau académique *
                </label>
                <select
                  id="academic_level"
                  name="academic_level"
                  value={formData.academic_level}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.academic_level ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                >
                  <option value="">Sélectionner un niveau</option>
                  {academicLevelOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                {errors.academic_level && (
                  <p className="mt-1 text-sm text-red-600">{errors.academic_level}</p>
                )}
              </div>
            </div>
          </div>

          {/* Study goals */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Objectifs d'étude
            </h3>
            <div className="grid grid-cols-1 gap-4">
              <Input
                label="Objectif hebdomadaire (heures) *"
                type="number"
                name="weekly_study_goal"
                value={formData.weekly_study_goal}
                onChange={handleChange}
                min="1"
                max="168"
                step="0.5"
                error={errors.weekly_study_goal}
                required
              />
              <p className="text-sm text-gray-600">
                Nombre d'heures que vous souhaitez étudier par semaine (entre 1 et 168 heures)
              </p>
            </div>
          </div>

          {/* Semester context */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Contexte du semestre
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Début du semestre"
                type="date"
                name="semester_start_date"
                value={formData.semester_start_date}
                onChange={handleChange}
              />
              <Input
                label="Fin du semestre"
                type="date"
                name="semester_end_date"
                value={formData.semester_end_date}
                onChange={handleChange}
              />
              <Input
                label="Début des examens"
                type="date"
                name="exam_period_start"
                value={formData.exam_period_start}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Time commitments */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Engagements de temps
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Heures de cours par semaine"
                type="number"
                name="total_course_hours_per_week"
                value={formData.total_course_hours_per_week}
                onChange={handleChange}
                min="0"
                max="168"
                step="0.5"
                placeholder="Ex: 20"
              />
              <Input
                label="Autres engagements (heures/semaine)"
                type="number"
                name="other_commitments_hours"
                value={formData.other_commitments_hours}
                onChange={handleChange}
                min="0"
                max="168"
                step="0.5"
                placeholder="Job, sport, associations..."
              />
            </div>
          </div>

          {/* Study preferences */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Préférences d'étude
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="preferred_study_time" className="block text-sm font-medium text-gray-700 mb-1">
                  Moment préféré
                </label>
                <select
                  id="preferred_study_time"
                  name="preferred_study_time"
                  value={formData.preferred_study_time}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionner</option>
                  <option value="morning">Matin</option>
                  <option value="afternoon">Après-midi</option>
                  <option value="evening">Soir</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>

              <div>
                <label htmlFor="preferred_session_duration" className="block text-sm font-medium text-gray-700 mb-1">
                  Durée de session (minutes)
                </label>
                <select
                  id="preferred_session_duration"
                  name="preferred_session_duration"
                  value={formData.preferred_session_duration}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionner</option>
                  <option value="45">45 min</option>
                  <option value="60">1 heure</option>
                  <option value="90">1h30</option>
                  <option value="120">2 heures</option>
                </select>
              </div>

              <div>
                <label htmlFor="study_pace" className="block text-sm font-medium text-gray-700 mb-1">
                  Rythme d'étude
                </label>
                <select
                  id="study_pace"
                  name="study_pace"
                  value={formData.study_pace}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionner</option>
                  <option value="intensive">Intensif</option>
                  <option value="balanced">Équilibré</option>
                  <option value="relaxed">Relax</option>
                </select>
              </div>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div className={`rounded-md p-4 ${
              message.type === 'success' ? 'bg-green-50' : 'bg-red-50'
            }`}>
              <div className="flex">
                <svg
                  className={`h-5 w-5 ${
                    message.type === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  {message.type === 'success' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <div className="ml-3">
                  <p className={`text-sm ${
                    message.type === 'success' ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {message.text}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Submit */}
          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="secondary"
              onClick={loadProfile}
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
              Enregistrer
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default ProfilePage;
