import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import apiClient from '../api/client';
import { useAuth } from './AuthContext';

const AcademicDataContext = createContext(null);

export const useAcademicData = () => {
  const context = useContext(AcademicDataContext);
  if (!context) {
    throw new Error('useAcademicData must be used within AcademicDataProvider');
  }
  return context;
};

export const AcademicDataProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  const [profile, setProfile] = useState(null);
  const [academicProfile, setAcademicProfile] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [exams, setExams] = useState([]);
  const [upcomingExams, setUpcomingExams] = useState([]);
  const [ectsProgression, setEctsProgression] = useState(null);
  const [ectsBreakdown, setEctsBreakdown] = useState(null);
  const [riskScores, setRiskScores] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [failedCourses, setFailedCourses] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchProfile = useCallback(async () => {
    try {
      const [profileRes, academicRes] = await Promise.all([
        apiClient.get('/api/v1/profile').catch(() => ({ data: null })),
        apiClient.get('/api/v1/academic/profile').catch(() => ({ data: null })),
      ]);
      setProfile(profileRes.data);
      setAcademicProfile(academicRes.data);
      return { profile: profileRes.data, academicProfile: academicRes.data };
    } catch (err) {
      console.error('Error fetching profiles:', err);
    }
  }, []);

  const updateAcademicProfile = useCallback(async (data) => {
    try {
      const res = await apiClient.put('/api/v1/academic/profile', data);
      setAcademicProfile(res.data);
      await fetchProfile();
      return res.data;
    } catch (err) {
      console.error('Error updating academic profile:', err);
      throw err;
    }
  }, [fetchProfile]);

  const updateStudentProfile = useCallback(async (data) => {
    try {
      const res = await apiClient.put('/api/v1/profile', data);
      setProfile(res.data);
      await fetchProfile();
      return res.data;
    } catch (err) {
      console.error('Error updating student profile:', err);
      throw err;
    }
  }, [fetchProfile]);

  const fetchSubjects = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/v1/subjects');
      const list = res.data?.subjects || [];
      setSubjects(list);
      return list;
    } catch (err) {
      console.error('Error fetching subjects:', err);
    }
  }, []);

  const fetchExams = useCallback(async () => {
    try {
      const [allRes, upcomingRes] = await Promise.all([
        apiClient.get('/api/v1/exams/all'),
        apiClient.get('/api/v1/exams'),
      ]);
      setExams(allRes.data?.exams || []);
      setUpcomingExams(upcomingRes.data?.exams || []);
      return { all: allRes.data?.exams || [], upcoming: upcomingRes.data?.exams || [] };
    } catch (err) {
      console.error('Error fetching exams:', err);
    }
  }, []);

  const fetchECTSProgression = useCallback(async () => {
    try {
      const [progRes, breakdownRes] = await Promise.all([
        apiClient.get('/api/v1/ects/progression'),
        apiClient.get('/api/v1/ects/progression/breakdown'),
      ]);
      setEctsProgression(progRes.data);
      setEctsBreakdown(breakdownRes.data);
      return { progression: progRes.data, breakdown: breakdownRes.data };
    } catch (err) {
      console.error('Error fetching ECTS progression:', err);
    }
  }, []);

  const fetchAnalysis = useCallback(async () => {
    try {
      const [riskRes, priorityRes, failedRes] = await Promise.all([
        apiClient.get('/api/v1/analysis/risk'),
        apiClient.get('/api/v1/analysis/priorities'),
        apiClient.get('/api/v1/analysis/failed-courses'),
      ]);
      setRiskScores(riskRes.data?.risk_scores || []);
      setPriorities(priorityRes.data?.priorities || []);
      setFailedCourses(failedRes.data?.failed_courses || []);
      return {
        riskScores: riskRes.data?.risk_scores || [],
        priorities: priorityRes.data?.priorities || [],
        failedCourses: failedRes.data?.failed_courses || []
      };
    } catch (err) {
      console.error('Error fetching analysis:', err);
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchProfile(),
        fetchSubjects(),
        fetchExams(),
        fetchECTSProgression(),
        fetchAnalysis(),
      ]);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, fetchProfile, fetchSubjects, fetchExams, fetchECTSProgression, fetchAnalysis]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  const createSubject = async (data) => {
    const res = await apiClient.post('/api/v1/subjects', data);
    await fetchSubjects();
    await fetchAnalysis();
    await fetchECTSProgression();
    return res.data;
  };

  const updateSubject = async (id, data) => {
    const res = await apiClient.put(`/api/v1/subjects/${id}`, data);
    await fetchSubjects();
    await fetchAnalysis();
    await fetchECTSProgression();
    return res.data;
  };

  const deleteSubject = async (id) => {
    await apiClient.delete(`/api/v1/subjects/${id}`);
    await fetchSubjects();
    await fetchAnalysis();
    await fetchECTSProgression();
  };

  const createExam = async (data) => {
    const res = await apiClient.post('/api/v1/exams', data);
    await fetchExams();
    await fetchAnalysis();
    return res.data;
  };

  const updateExam = async (id, data) => {
    const res = await apiClient.put(`/api/v1/exams/${id}`, data);
    await fetchExams();
    await fetchAnalysis();
    return res.data;
  };

  const deleteExam = async (id) => {
    await apiClient.delete(`/api/v1/exams/${id}`);
    await fetchExams();
    await fetchAnalysis();
  };

  const recalculateAnalysis = async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/v1/analysis/recalculate');
      await fetchECTSProgression();
      await fetchAnalysis();
    } catch (err) {
      console.error('Error recalculating analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    profile,
    academicProfile,
    subjects,
    exams,
    upcomingExams,
    ectsProgression,
    ectsBreakdown,
    riskScores,
    priorities,
    failedCourses,
    loading,
    error,
    fetchProfile,
    updateAcademicProfile,
    updateStudentProfile,
    fetchSubjects,
    fetchExams,
    fetchECTSProgression,
    fetchAnalysis,
    fetchAllData,
    createSubject,
    updateSubject,
    deleteSubject,
    createExam,
    updateExam,
    deleteExam,
    recalculateAnalysis
  };

  return (
    <AcademicDataContext.Provider value={value}>
      {children}
    </AcademicDataContext.Provider>
  );
};

AcademicDataProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
