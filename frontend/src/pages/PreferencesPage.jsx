import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import apiClient from '../api/client';
import { formatApiError } from '../utils/errorUtils';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const SectionTitle = ({ children }) => (
  <h3 className="form-section-title text-violet-400">{children}</h3>
);

// German Wiederholung rules: which semesters can be retaken per current semester
const RETAKE_RULES = {
  1: [],
  2: [],
  3: [],
  4: [2],
  5: [1, 3],
  6: [2, 4],
};

const getAllowedRetakes = (semNum) => {
  const sem = parseInt(semNum) || 1;
  if (RETAKE_RULES[sem]) return RETAKE_RULES[sem];
  if (sem >= 7) {
    const allowed = [];
    for (let s = 1; s < sem; s++) {
      allowed.push(s);
    }
    return allowed;
  }
  return [];
};

const PreferencesPage = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  // Reference data lists
  const [universities, setUniversities] = useState([]);
  const [filieres, setFilieres] = useState([]);
  const [cursusList, setCursusList] = useState([]);

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
    preferences: {
      ects_target: 180.0,
      personal_goals: ''
    },
  });

  const [academicData, setAcademicData] = useState({
    university_id: '',
    filiere_id: '',
    cursus_id: '',
    current_semester: 1,
    academic_year: new Date().getFullYear(),
    retake_semesters: [],
  });

  const [errors, setErrors] = useState({});

  const academicLevelOptions = ['Bachelor', 'Master', 'PhD', 'Other'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileRes, academicProfileRes, univsRes] = await Promise.all([
        apiClient.get('/api/v1/profile').catch(() => ({ data: null })),
        apiClient.get('/api/v1/academic/profile').catch(() => ({ data: null })),
        apiClient.get('/api/v1/academic/universities').catch(() => ({ data: [] })),
      ]);

      setUniversities(univsRes.data || []);

      if (profileRes.data) {
        const student = profileRes.data;
        const preferences = student.preferences || {};
        
        setFormData({
          cursus: student.cursus || '',
          academic_level: student.academic_level || '',
          weekly_study_goal: student.weekly_study_goal || 20,
          semester_start_date: student.semester_start_date || '',
          semester_end_date: student.semester_end_date || '',
          exam_period_start: student.exam_period_start || '',
          total_course_hours_per_week: student.total_course_hours_per_week || '',
          other_commitments_hours: student.other_commitments_hours || '',
          preferred_study_time: student.preferred_study_time || '',
          preferred_session_duration: student.preferred_session_duration || '',
          study_pace: student.study_pace || '',
          preferences: {
            ects_target: preferences.ects_target || 180.0,
            personal_goals: preferences.personal_goals || ''
          },
        });
      }

      if (academicProfileRes.data) {
        const acad = academicProfileRes.data;
        setAcademicData({
          university_id: acad.university_id || '',
          filiere_id: acad.filiere_id || '',
          cursus_id: acad.cursus_id || '',
          current_semester: acad.current_semester || 1,
          academic_year: acad.academic_year || new Date().getFullYear(),
          retake_semesters: acad.retake_semesters || [],
        });

        if (acad.university_id) {
          const filieresRes = await apiClient.get(`/api/v1/academic/filieres?university_id=${acad.university_id}`);
          setFilieres(filieresRes.data || []);
        }
        if (acad.filiere_id) {
          const cursusRes = await apiClient.get(`/api/v1/academic/cursus?filiere_id=${acad.filiere_id}`);
          const fetchedCursusList = cursusRes.data || [];
          setCursusList(fetchedCursusList);
          
          if (!profileRes.data?.cursus && acad.cursus_id) {
            const foundTrack = fetchedCursusList.find((c) => c.id === acad.cursus_id);
            if (foundTrack) {
              setFormData((prev) => ({ ...prev, cursus: foundTrack.name }));
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading academic preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUniversityChange = async (e) => {
    const uniId = e.target.value ? parseInt(e.target.value) : '';
    setAcademicData(prev => ({
      ...prev,
      university_id: uniId,
      filiere_id: '',
      cursus_id: '',
    }));
    setFilieres([]);
    setCursusList([]);

    if (uniId) {
      try {
        const res = await apiClient.get(`/api/v1/academic/filieres?university_id=${uniId}`);
        setFilieres(res.data || []);
      } catch (err) {
        console.error('Error fetching filieres:', err);
      }
    }
  };

  const handleFiliereChange = async (e) => {
    const filId = e.target.value ? parseInt(e.target.value) : '';
    setAcademicData(prev => ({
      ...prev,
      filiere_id: filId,
      cursus_id: '',
    }));
    setCursusList([]);

    if (filId) {
      try {
        const res = await apiClient.get(`/api/v1/academic/cursus?filiere_id=${filId}`);
        setCursusList(res.data || []);
      } catch (err) {
        console.error('Error fetching cursus:', err);
      }
    }
  };

  const handleCursusChange = (e) => {
    const curId = e.target.value ? parseInt(e.target.value) : '';
    const selectedTrack = cursusList.find((c) => c.id === curId);
    setAcademicData((prev) => ({
      ...prev,
      cursus_id: curId,
    }));
    if (selectedTrack) {
      setFormData((prev) => ({
        ...prev,
        cursus: selectedTrack.name,
      }));
    }
  };

  const handleAcademicFieldChange = (e) => {
    const { name, value } = e.target;
    setAcademicData(prev => ({
      ...prev,
      [name]: name === 'current_semester' || name === 'academic_year' ? parseInt(value) || value : value,
    }));
  };

  const handleRetakeSemesterToggle = (semNumber) => {
    setAcademicData(prev => {
      const current = prev.retake_semesters || [];
      const updated = current.includes(semNumber)
        ? current.filter(s => s !== semNumber)
        : [...current, semNumber].sort((a, b) => a - b);
      return { ...prev, retake_semesters: updated };
    });
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handlePrefChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [name]: type === 'number' ? (value === '' ? '' : parseFloat(value)) : value,
      }
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.weekly_study_goal || formData.weekly_study_goal < 1) {
      newErrors.weekly_study_goal = 'Weekly study goal must be at least 1 hour';
    }
    if (!formData.academic_level) {
      newErrors.academic_level = 'Academic level is required';
    }

    const ectsTarget = formData.preferences.ects_target;
    if (ectsTarget !== undefined && (ectsTarget <= 0 || isNaN(ectsTarget))) {
      newErrors.ects_target = 'ECTS target must be a positive number';
    }

    const sem = academicData.current_semester;
    if (sem !== undefined && (sem < 1 || sem > 7)) {
      newErrors.current_semester = 'Current semester must be between S1 and S7';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSaving(true);
    setMessage(null);
    try {
      const cleanedStudentData = { ...formData };
      ['semester_start_date', 'semester_end_date', 'exam_period_start', 'total_course_hours_per_week', 'other_commitments_hours', 'preferred_study_time', 'preferred_session_duration', 'study_pace'].forEach((f) => {
        if (cleanedStudentData[f] === '') cleanedStudentData[f] = null;
      });

      // Ensure numeric fields are properly typed or null
      if (cleanedStudentData.preferred_session_duration) {
        cleanedStudentData.preferred_session_duration = parseInt(cleanedStudentData.preferred_session_duration, 10) || null;
      }
      if (cleanedStudentData.total_course_hours_per_week !== null && cleanedStudentData.total_course_hours_per_week !== undefined) {
        const val = parseFloat(cleanedStudentData.total_course_hours_per_week);
        cleanedStudentData.total_course_hours_per_week = isNaN(val) ? null : val;
      }
      if (cleanedStudentData.other_commitments_hours !== null && cleanedStudentData.other_commitments_hours !== undefined) {
        const val = parseFloat(cleanedStudentData.other_commitments_hours);
        cleanedStudentData.other_commitments_hours = isNaN(val) ? null : val;
      }

      // Guarantee non-empty cursus required by student profile
      let cursusName = (cleanedStudentData.cursus || '').trim();
      if (!cursusName && academicData.cursus_id) {
        const found = cursusList.find((c) => c.id === academicData.cursus_id);
        if (found) cursusName = found.name;
      }
      if (!cursusName && academicData.filiere_id) {
        const foundFil = filieres.find((f) => f.id === academicData.filiere_id);
        if (foundFil) cursusName = foundFil.name;
      }
      if (!cursusName) {
        cursusName = cleanedStudentData.academic_level ? `${cleanedStudentData.academic_level} Standard` : 'Général';
      }
      cleanedStudentData.cursus = cursusName;

      await apiClient.post('/api/v1/profile', cleanedStudentData);

      if (academicData.university_id && academicData.filiere_id && academicData.cursus_id) {
        await apiClient.put('/api/v1/academic/profile', {
          university_id: academicData.university_id,
          filiere_id: academicData.filiere_id,
          cursus_id: academicData.cursus_id,
          current_semester: academicData.current_semester,
          academic_year: academicData.academic_year,
          retake_semesters: academicData.retake_semesters || [],
        });
      }

      setMessage({ type: 'success', text: t('preferences.success_saved', 'Profil académique et préférences enregistrés avec succès !') });
      await loadData();
    } catch (error) {
      console.error('Error saving profile:', error);
      setMessage({
        type: 'error',
        text: formatApiError(error, t('preferences.error_saved', 'Erreur lors de l\'enregistrement des modifications.')),
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-2xl font-bold text-white shadow-glow-sm">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">
              <span>{t('preferences.title', 'Profil Académique & Préférences')}</span>
              <Badge variant="violet">{t('nav.student_portal', 'Étudiant')}</Badge>
            </h1>
            <p className="text-white/40 text-sm">{user?.email}</p>
          </div>
        </div>
        <p className="text-white/40 text-sm">
          {t('preferences.subtitle', 'Configurez votre filière, cursus, objectifs d\'heures et rythme d\'apprentissage.')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Academic Affiliation */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>{t('preferences.section.academic', 'Hiérarchie Académique')}</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <div>
              <label htmlFor="university_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                {t('preferences.university', 'Université')}
              </label>
              <select
                id="university_id"
                name="university_id"
                value={academicData.university_id}
                onChange={handleUniversityChange}
              >
                <option value="">{t('preferences.university', 'Sélectionnez votre université')}</option>
                {universities.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filiere_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                {t('preferences.filiere', 'Programme d\'études (Filière)')}
              </label>
              <select
                id="filiere_id"
                name="filiere_id"
                value={academicData.filiere_id}
                onChange={handleFiliereChange}
                disabled={!academicData.university_id}
              >
                <option value="">{t('preferences.filiere', 'Sélectionnez une filière')}</option>
                {filieres.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="cursus_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                {t('preferences.cursus', 'Parcours académique (Cursus)')}
              </label>
              <select
                id="cursus_id"
                name="cursus_id"
                value={academicData.cursus_id}
                onChange={handleCursusChange}
                disabled={!academicData.filiere_id}
              >
                <option value="">{t('preferences.cursus', 'Sélectionnez un parcours')}</option>
                {cursusList.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="current_semester" className="block text-sm font-semibold text-white/70 mb-1.5">
                  {t('preferences.current_semester', 'Semestre actuel')}
                </label>
                <select
                  id="current_semester"
                  name="current_semester"
                  value={academicData.current_semester}
                  onChange={handleAcademicFieldChange}
                >
                  {[1, 2, 3, 4, 5, 6, 7].map((num) => (
                    <option key={num} value={num}>S{num}{num === 7 ? ' (Étendu)' : ''}</option>
                  ))}
                </select>
                {errors.current_semester && (
                  <p className="mt-1 text-xs text-red-400">{errors.current_semester}</p>
                )}
              </div>

              <div>
                <label htmlFor="academic_year" className="block text-sm font-semibold text-white/70 mb-1.5">
                  {t('preferences.academic_year', 'Année académique')}
                </label>
                <input
                  type="number"
                  id="academic_year"
                  name="academic_year"
                  value={academicData.academic_year}
                  onChange={handleAcademicFieldChange}
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all"
                  min="2020"
                  max="2100"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Retake Semesters (German Wiederholung system) */}
        {(() => {
          const currentSem = parseInt(academicData.current_semester) || 1;
          const allowedRetakes = getAllowedRetakes(currentSem);
          if (allowedRetakes.length === 0) return null;

          return (
            <Card className="p-6 border border-amber-200 bg-amber-50/50 dark:border-amber-500/20 dark:bg-amber-500/[0.04]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-amber-800 dark:text-amber-450 text-sm font-bold">⚠</span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-amber-900 dark:text-amber-300">{t('preferences.retake_semesters', 'Semestres en Rattrapage (Wiederholung)')}</h3>
                  <p className="text-xs text-amber-700 dark:text-amber-400/70 mt-0.5">
                    Semestres antérieurs disponibles pour rattrapage (S{currentSem}).
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                {allowedRetakes.map((semNum) => {
                  const isChecked = (academicData.retake_semesters || []).includes(semNum);
                  return (
                    <label
                      key={semNum}
                      htmlFor={`retake-s${semNum}`}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-xl border cursor-pointer transition-all duration-200 select-none
                        ${isChecked
                          ? 'bg-amber-100/60 border-amber-300 text-amber-900 dark:bg-amber-500/20 dark:border-amber-500/40 dark:text-amber-200'
                          : 'bg-slate-50 border-slate-100/80 text-slate-650 hover:border-amber-300 hover:bg-amber-50/50 dark:bg-white/[0.03] dark:border-white/10 dark:text-white/60 dark:hover:border-amber-500/30 dark:hover:bg-amber-500/5'
                        }
                      `}
                    >
                      <input
                        type="checkbox"
                        id={`retake-s${semNum}`}
                        checked={isChecked}
                        onChange={() => handleRetakeSemesterToggle(semNum)}
                        className="sr-only"
                      />
                      <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all
                        ${isChecked ? 'bg-amber-600 border-amber-500 dark:bg-amber-500 dark:border-amber-400' : 'border-slate-300 dark:border-white/20'}`}
                      >
                        {isChecked && (
                          <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <span className="text-sm font-bold">Semestre S{semNum}</span>
                        <p className="text-xs text-slate-500 dark:text-white/40 mt-0.5">{t('subjects.status.retake', 'Rattrapage')} S{semNum}</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </Card>
          );
        })()}

        {/* Graduation Goals */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>{t('preferences.section.goals', 'Objectifs d\'étude & Charge de travail')}</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
            <div className="md:col-span-1">
              <Input
                label={`${t('preferences.ects_target', 'Objectif total ECTS')} *`}
                type="number"
                name="ects_target"
                value={formData.preferences.ects_target}
                onChange={handlePrefChange}
                error={errors.ects_target}
                required
              />
            </div>
            
            <div className="md:col-span-2">
              <label htmlFor="personal_goals" className="block text-sm font-semibold text-white/70 mb-1.5">
                {t('label.notes', 'Objectifs personnels')}
              </label>
              <textarea
                id="personal_goals"
                name="personal_goals"
                value={formData.preferences.personal_goals}
                onChange={handlePrefChange}
                rows={3}
                className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all text-sm"
                placeholder="Ex: Valider avec mention, préparer mon stage..."
              />
            </div>
          </div>
        </Card>

        {/* Study Preferences */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>{t('preferences.section.habits', 'Habitudes & Rythme d\'apprentissage')}</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <div>
              <Input
                label={`${t('preferences.weekly_goal', 'Objectif d\'étude hebdomadaire (heures)')} *`}
                type="number"
                name="weekly_study_goal"
                value={formData.weekly_study_goal}
                onChange={handleChange}
                min="1" max="168" step="0.5"
                error={errors.weekly_study_goal}
                required
              />
            </div>

            <div>
              <label htmlFor="academic_level" className="block text-sm font-semibold text-white/70 mb-1.5">
                {t('preferences.academic_level', 'Niveau académique')} *
              </label>
              <select
                id="academic_level"
                name="academic_level"
                value={formData.academic_level}
                onChange={handleChange}
                required
              >
                <option value="">{t('preferences.academic_level', 'Sélectionner')}</option>
                {academicLevelOptions.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
              {errors.academic_level && (
                <p className="mt-1 text-xs text-red-400">{errors.academic_level}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 md:col-span-2 gap-4">
              <div>
                <label htmlFor="preferred_study_time" className="block text-sm font-semibold text-white/70 mb-1.5">
                  {t('preferences.preferred_time', 'Moment d\'étude')}
                </label>
                <select
                  id="preferred_study_time"
                  name="preferred_study_time"
                  value={formData.preferred_study_time}
                  onChange={handleChange}
                >
                  <option value="">{t('label.optional', 'Optionnel')}</option>
                  <option value="morning">{t('preferences.time.morning', 'Matin (08:00 - 12:00)')}</option>
                  <option value="afternoon">{t('preferences.time.afternoon', 'Après-midi (13:00 - 17:00)')}</option>
                  <option value="evening">{t('preferences.time.evening', 'Soirée (18:00 - 22:00)')}</option>
                  <option value="night">{t('preferences.time.night', 'Nuit (22:00+)')}</option>
                </select>
              </div>

              <div>
                <label htmlFor="preferred_session_duration" className="block text-sm font-semibold text-white/70 mb-1.5">
                  {t('preferences.preferred_duration', 'Durée de session')}
                </label>
                <select
                  id="preferred_session_duration"
                  name="preferred_session_duration"
                  value={formData.preferred_session_duration}
                  onChange={handleChange}
                >
                  <option value="">{t('label.optional', 'Optionnel')}</option>
                  <option value="45">45 min</option>
                  <option value="60">1h00</option>
                  <option value="90">1h30</option>
                  <option value="120">2h00</option>
                </select>
              </div>

              <div>
                <label htmlFor="study_pace" className="block text-sm font-semibold text-white/70 mb-1.5">
                  {t('preferences.pace', 'Rythme d\'étude')}
                </label>
                <select
                  id="study_pace"
                  name="study_pace"
                  value={formData.study_pace}
                  onChange={handleChange}
                >
                  <option value="">{t('label.optional', 'Optionnel')}</option>
                  <option value="intensive">{t('preferences.pace.intensive', 'Intensif')}</option>
                  <option value="moderate">{t('preferences.pace.moderate', 'Modéré')}</option>
                  <option value="relaxed">{t('preferences.pace.relaxed', 'Détendu')}</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        {/* Semester Calendar & Constraints */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>{t('preferences.section.calendar', 'Calendrier & Dates Clés')}</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <Input label={t('preferences.semester_start', 'Début du semestre')} type="date" name="semester_start_date" value={formData.semester_start_date} onChange={handleChange} />
            <Input label={t('preferences.semester_end', 'Fin du semestre')} type="date" name="semester_end_date" value={formData.semester_end_date} onChange={handleChange} />
            <Input label={t('preferences.exam_start', 'Session d\'examens')} type="date" name="exam_period_start" value={formData.exam_period_start} onChange={handleChange} />
          </div>
        </Card>

        {/* Message Indicator */}
        {message && (
          <div className={`rounded-xl p-4 flex items-center gap-3 border shadow-lg ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-red-500/10 border-red-500/20 text-red-300'
          }`}>
            <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {message.type === 'success'
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              }
            </svg>
            <p className="text-sm font-semibold">{message.text}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between items-center gap-3 border-t border-white/5 pt-4">
          <Button type="button" variant="ghost" onClick={loadData} disabled={saving}>
            {t('action.cancel', 'Annuler')}
          </Button>
          <div className="flex items-center gap-3">
            <Button type="submit" variant="primary" loading={saving} disabled={saving} size="lg">
              {t('action.save', 'Enregistrer')}
            </Button>
            {message?.type === 'success' && (
              <Button
                type="button"
                variant="secondary"
                size="lg"
                onClick={() => navigate('/subjects')}
              >
                {t('subjects.title', 'Mes cours')} →
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

export default PreferencesPage;
