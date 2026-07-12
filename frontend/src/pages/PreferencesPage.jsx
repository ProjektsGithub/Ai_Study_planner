import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const SectionTitle = ({ children }) => (
  <h3 className="form-section-title text-violet-400">{children}</h3>
);

const PreferencesPage = () => {
  const { user } = useAuth();
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
        });

        if (acad.university_id) {
          const filieresRes = await apiClient.get(`/api/v1/academic/filieres?university_id=${acad.university_id}`);
          setFilieres(filieresRes.data || []);
        }
        if (acad.filiere_id) {
          const cursusRes = await apiClient.get(`/api/v1/academic/cursus?filiere_id=${acad.filiere_id}`);
          setCursusList(cursusRes.data || []);
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
        console.error('Error loading study programs:', err);
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
        console.error('Error loading academic tracks:', err);
      }
    }
  };

  const handleCursusChange = (e) => {
    const curId = e.target.value ? parseInt(e.target.value) : '';
    setAcademicData(prev => ({
      ...prev,
      cursus_id: curId,
    }));

    const selectedCursusObj = cursusList.find(c => c.id === curId);
    if (selectedCursusObj) {
      setFormData(prev => ({
        ...prev,
        cursus: selectedCursusObj.name
      }));
    }
  };

  const handleAcademicFieldChange = (e) => {
    const { name, value } = e.target;
    setAcademicData(prev => ({
      ...prev,
      [name]: value === '' ? '' : parseInt(value)
    }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numericFields = ['weekly_study_goal', 'total_course_hours_per_week', 'other_commitments_hours', 'preferred_session_duration'];
    setFormData((prev) => ({
      ...prev,
      [name]: numericFields.includes(name) ? (value === '' ? '' : parseFloat(value)) : value,
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const handlePrefChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [name]: name === 'ects_target' ? (value === '' ? '' : parseFloat(value)) : value
      }
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.academic_level) newErrors.academic_level = 'Academic level is required';
    if (!formData.weekly_study_goal) newErrors.weekly_study_goal = 'Weekly study goal is required';
    else if (formData.weekly_study_goal < 1 || formData.weekly_study_goal > 168) newErrors.weekly_study_goal = 'Must be between 1 and 168 hours';

    const ectsTarget = formData.preferences.ects_target;
    if (ectsTarget !== undefined && (ectsTarget <= 0 || isNaN(ectsTarget))) {
      newErrors.ects_target = 'ECTS target must be a positive number';
    }

    const sem = academicData.current_semester;
    if (sem !== undefined && (sem < 1 || sem > 6)) {
      newErrors.current_semester = 'Current semester must be between S1 and S6';
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

      await apiClient.post('/api/v1/profile', cleanedStudentData);

      if (academicData.university_id && academicData.filiere_id && academicData.cursus_id) {
        await apiClient.put('/api/v1/academic/profile', {
          university_id: academicData.university_id,
          filiere_id: academicData.filiere_id,
          cursus_id: academicData.cursus_id,
          current_semester: academicData.current_semester,
          academic_year: academicData.academic_year
        });
      }

      setMessage({ type: 'success', text: 'Academic profile and preferences saved successfully!' });
      await loadData();
    } catch (error) {
      console.error('Error saving profile:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Error saving changes.' });
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
        {/* Onboarding step pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs font-semibold text-violet-300 mb-4">
          <span className="w-5 h-5 rounded-full bg-violet-500/30 flex items-center justify-center text-[10px] font-bold">1</span>
          Step 1 of 4 — Academic Profile
        </div>
        <div className="flex items-center gap-4 mb-2">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-2xl font-bold text-white shadow-glow-sm">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">
              <span>My Academic Profile</span>
              <Badge variant="violet">Student</Badge>
            </h1>
            <p className="text-white/40 text-sm">{user?.email}</p>
          </div>
        </div>
        <p className="text-white/40 text-sm">
          Choose your university, program, and study preferences so the AI can personalize your plan.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Academic Affiliation */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>University Affiliation</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <div>
              <label htmlFor="university_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                University
              </label>
              <select
                id="university_id"
                name="university_id"
                value={academicData.university_id}
                onChange={handleUniversityChange}
              >
                <option value="">Select your university</option>
                {universities.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filiere_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                Study Program (Filière)
              </label>
              <select
                id="filiere_id"
                name="filiere_id"
                value={academicData.filiere_id}
                onChange={handleFiliereChange}
                disabled={!academicData.university_id}
              >
                <option value="">Select a program</option>
                {filieres.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="cursus_id" className="block text-sm font-semibold text-white/70 mb-1.5">
                Academic Track (Cursus)
              </label>
              <select
                id="cursus_id"
                name="cursus_id"
                value={academicData.cursus_id}
                onChange={handleCursusChange}
                disabled={!academicData.filiere_id}
              >
                <option value="">Select a track</option>
                {cursusList.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="current_semester" className="block text-sm font-semibold text-white/70 mb-1.5">
                  Current Semester
                </label>
                <select
                  id="current_semester"
                  name="current_semester"
                  value={academicData.current_semester}
                  onChange={handleAcademicFieldChange}
                >
                  {[1, 2, 3, 4, 5, 6].map((num) => (
                    <option key={num} value={num}>Semester S{num}</option>
                  ))}
                </select>
                {errors.current_semester && (
                  <p className="mt-1 text-xs text-red-400">{errors.current_semester}</p>
                )}
              </div>

              <div>
                <label htmlFor="academic_year" className="block text-sm font-semibold text-white/70 mb-1.5">
                  Academic Year
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

        {/* Graduation Goals */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>Graduation Goals</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
            <div className="md:col-span-1">
              <Input
                label="Total ECTS Target *"
                type="number"
                name="ects_target"
                value={formData.preferences.ects_target}
                onChange={handlePrefChange}
                error={errors.ects_target}
                required
              />
              <p className="text-[11px] text-white/30 mt-1">Required credits (e.g., 180 for Bachelor)</p>
            </div>
            
            <div className="md:col-span-2">
              <label htmlFor="personal_goals" className="block text-sm font-semibold text-white/70 mb-1.5">
                Personal Academic Goals
              </label>
              <textarea
                id="personal_goals"
                name="personal_goals"
                value={formData.preferences.personal_goals}
                onChange={handlePrefChange}
                rows={3}
                className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all text-sm"
                placeholder="e.g., Graduate with honors, prepare for my internship..."
              />
            </div>
          </div>
        </Card>

        {/* Study Preferences */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>AI Study Configuration</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
            <div>
              <Input
                label="Weekly Study Goal (hours) *"
                type="number"
                name="weekly_study_goal"
                value={formData.weekly_study_goal}
                onChange={handleChange}
                min="1" max="168" step="0.5"
                error={errors.weekly_study_goal}
                required
              />
              <p className="text-[11px] text-white/30 mt-1">Number of personal study hours per week</p>
            </div>

            <div>
              <label htmlFor="academic_level" className="block text-sm font-semibold text-white/70 mb-1.5">
                General Academic Level *
              </label>
              <select
                id="academic_level"
                name="academic_level"
                value={formData.academic_level}
                onChange={handleChange}
                required
              >
                <option value="">Select</option>
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
                  Preferred Study Time
                </label>
                <select
                  id="preferred_study_time"
                  name="preferred_study_time"
                  value={formData.preferred_study_time}
                  onChange={handleChange}
                >
                  <option value="">Select</option>
                  <option value="morning">Morning</option>
                  <option value="afternoon">Afternoon</option>
                  <option value="evening">Evening</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>

              <div>
                <label htmlFor="preferred_session_duration" className="block text-sm font-semibold text-white/70 mb-1.5">
                  Session Duration
                </label>
                <select
                  id="preferred_session_duration"
                  name="preferred_session_duration"
                  value={formData.preferred_session_duration}
                  onChange={handleChange}
                >
                  <option value="">Select</option>
                  <option value="45">45 min</option>
                  <option value="60">1 hour</option>
                  <option value="90">1h30</option>
                  <option value="120">2 hours</option>
                </select>
              </div>

              <div>
                <label htmlFor="study_pace" className="block text-sm font-semibold text-white/70 mb-1.5">
                  Study Pace
                </label>
                <select
                  id="study_pace"
                  name="study_pace"
                  value={formData.study_pace}
                  onChange={handleChange}
                >
                  <option value="">Select</option>
                  <option value="intensive">Intensive</option>
                  <option value="balanced">Balanced</option>
                  <option value="relaxed">Relaxed</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        {/* Semester Calendar & Constraints */}
        <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
          <SectionTitle>Semester Calendar & Commitments</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <Input label="Semester Start Date" type="date" name="semester_start_date" value={formData.semester_start_date} onChange={handleChange} />
            <Input label="Semester End Date" type="date" name="semester_end_date" value={formData.semester_end_date} onChange={handleChange} />
            <Input label="Exam Period Start" type="date" name="exam_period_start" value={formData.exam_period_start} onChange={handleChange} />

            <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              <Input
                label="In-Person Class Hours / Week"
                type="number"
                name="total_course_hours_per_week"
                value={formData.total_course_hours_per_week}
                onChange={handleChange}
                min="0" max="168" step="0.5"
                placeholder="e.g. 24"
              />
              <Input
                label="Other Commitments (Job, Sport, Clubs...) Hours / Week"
                type="number"
                name="other_commitments_hours"
                value={formData.other_commitments_hours}
                onChange={handleChange}
                min="0" max="168" step="0.5"
                placeholder="e.g. 10"
              />
            </div>
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
            Cancel
          </Button>
          <div className="flex items-center gap-3">
            <Button type="submit" variant="primary" loading={saving} disabled={saving} size="lg">
              Save Changes
            </Button>
            {message?.type === 'success' && (
              <Button
                type="button"
                variant="secondary"
                size="lg"
                onClick={() => navigate('/subjects')}
              >
                Next: Select Courses →
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

export default PreferencesPage;
