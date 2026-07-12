import { useState } from 'react';
import PropTypes from 'prop-types';
import SubjectCard from './SubjectCard';

const SubjectList = ({ subjects = [], riskScores = [], onEdit, onDelete }) => {
  const [filterSemester, setFilterSemester] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [sortBy, setSortBy] = useState('name');

  // Semester dropdown list (from subjects)
  const semesters = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'];

  const getSubjectRisk = (subjectId) => {
    return riskScores.find((r) => r.course_id === subjectId);
  };

  const filteredSubjects = subjects
    .filter((subject) => {
      const risk = getSubjectRisk(subject.id);
      
      const matchSemester = !filterSemester || (subject.semester === filterSemester);
      const matchStatus = !filterStatus || (subject.validation_status === filterStatus);
      const matchRisk = !filterRisk || (risk?.risk_level === filterRisk);

      return matchSemester && matchStatus && matchRisk;
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }
      if (sortBy === 'ects') {
        return (b.ects_credits ?? 0) - (a.ects_credits ?? 0);
      }
      if (sortBy === 'risk') {
        const riskA = getSubjectRisk(a.id)?.risk_level || 'low';
        const riskB = getSubjectRisk(b.id)?.risk_level || 'low';
        
        const riskWeights = { high: 3, medium: 2, low: 1 };
        return riskWeights[riskB] - riskWeights[riskA];
      }
      return 0;
    });

  return (
    <div className="space-y-6">
      {/* Filtering and Sorting Panel */}
      <div className="p-5 rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-md flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-3 flex-1 min-w-[280px]">
          {/* Semester Filter */}
          <div className="w-[140px]">
            <select
              value={filterSemester}
              onChange={(e) => setFilterSemester(e.target.value)}
              aria-label="Filter by semester"
            >
              <option value="">All Semesters</option>
              {semesters.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-[140px]">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              aria-label="Filter by status"
            >
              <option value="">All Statuses</option>
              <option value="not_started">Not Started</option>
              <option value="in_progress">In Progress</option>
              <option value="validated">Validated</option>
              <option value="failed">Failed / Retake</option>
            </select>
          </div>

          {/* Risk Filter */}
          <div className="w-[140px]">
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              aria-label="Filter by risk"
            >
              <option value="">All Risks</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
            </select>
          </div>
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-xs text-white/40 font-semibold uppercase tracking-wider whitespace-nowrap">Sort by</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-[120px]"
            aria-label="Sort by"
          >
            <option value="name">Name</option>
            <option value="ects">ECTS</option>
            <option value="risk">Risk Level</option>
          </select>
        </div>
      </div>

      {/* Grid Display */}
      {filteredSubjects.length === 0 ? (
        <div className="empty-state">
          <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13" />
            </svg>
          </div>
          <h3 className="text-white/60 font-semibold mb-1">No subjects found</h3>
          <p className="text-white/30 text-xs">Adjust your filters or add a new subject.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
          {filteredSubjects.map((subject) => (
            <SubjectCard
              key={subject.id}
              subject={subject}
              riskScore={getSubjectRisk(subject.id)}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

SubjectList.propTypes = {
  subjects: PropTypes.array.isRequired,
  riskScores: PropTypes.array,
  onEdit: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default SubjectList;
