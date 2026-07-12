import { useState, useEffect } from 'react';
import { useAcademicData } from '../context/AcademicDataContext';
import SemesterTimeline from '../components/progression/SemesterTimeline';
import SubjectValidationStatus from '../components/progression/SubjectValidationStatus';
import ECTSBreakdown from '../components/progression/ECTSBreakdown';
import Card from '../components/ui/Card';
import ProgressBar from '../components/ui/ProgressBar';

const ProgressionPage = () => {
  const {
    subjects,
    ectsProgression,
    ectsBreakdown,
    academicProfile,
    fetchECTSProgression,
    loading
  } = useAcademicData();

  const [selectedSemester, setSelectedSemester] = useState('S1');

  useEffect(() => {
    fetchECTSProgression();
  }, [fetchECTSProgression]);

  // Current semester from profile (default to 1)
  const currentSemesterNum = academicProfile?.current_semester || 1;

  // Filter subjects for the selected semester
  const semesterSubjects = subjects.filter((s) => s.semester === selectedSemester);

  const obtained = ectsProgression?.ects_obtained || 0;
  const target = ectsProgression?.ects_required || 180.0;

  // Map backend breakdown format to the format required by ECTSBreakdown
  // Backend returns: list of structures containing semester, obtained, total
  const mappedBreakdown = ectsBreakdown?.by_semester?.map(b => ({
    semester: b.semester,
    obtained: b.obtained,
    total: b.total
  })) || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-1.5">Academic Progression</h1>
        <p className="text-white/40 text-sm">Visualize your ECTS credits and progress throughout your program.</p>
      </div>

      {/* Graduation progression overview card */}
      <Card className="mb-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-600 to-indigo-500" />
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex-1">
            <h2 className="text-lg font-bold text-white mb-1">Graduation Goal</h2>
            <p className="text-white/40 text-xs">Cumulative progress across your studies</p>
          </div>
          <div className="flex items-baseline gap-2.5 flex-shrink-0">
            <span className="text-4xl font-extrabold text-white">{obtained.toFixed(1)}</span>
            <span className="text-sm text-white/30">/ {target.toFixed(1)} ECTS obtained</span>
          </div>
        </div>
        <div className="mt-6">
          <ProgressBar value={obtained} max={target} showLabel={false} />
        </div>
      </Card>

      {/* Timeline Selector */}
      <Card className="mb-8 p-4">
        <SemesterTimeline
          selectedSemester={selectedSemester}
          onSemesterSelect={setSelectedSemester}
          currentSemester={currentSemesterNum}
        />
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Selected semester detail list */}
        <Card className="lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-white">Subjects of {selectedSemester}</h2>
            <span className="text-xs text-white/40">{semesterSubjects.length} subject(s)</span>
          </div>

          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-8 h-8 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
            </div>
          ) : semesterSubjects.length === 0 ? (
            <div className="empty-state py-12">
              <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13" />
                </svg>
              </div>
              <p className="text-sm text-white/50">No subjects registered for this semester.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {semesterSubjects.map((sub) => (
                <SubjectValidationStatus key={sub.id} subject={sub} />
              ))}
            </div>
          )}
        </Card>

        {/* ECTS Breakdown sidebar */}
        <Card>
          <h2 className="text-lg font-bold text-white mb-6">Breakdown by Semester</h2>
          <ECTSBreakdown breakdown={mappedBreakdown} />
        </Card>
      </div>
    </div>
  );
};

export default ProgressionPage;
