import { useState, useEffect, useMemo } from 'react';
import { useAcademicData } from '../context/AcademicDataContext';
import PriorityList from '../components/recommendations/PriorityList';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Skeleton from '../components/ui/Skeleton';

const RecommendationsPage = () => {
  const {
    priorities,
    riskScores,
    failedCourses,
    ectsProgression,
    upcomingExams,
    recalculateAnalysis,
    loading
  } = useAcademicData();

  const [dismissedIds, setDismissedIds] = useState(() => {
    const saved = localStorage.getItem('dismissed_recommendations');
    return saved ? JSON.parse(saved) : [];
  });

  const [freshnessTime, setFreshnessTime] = useState(() => {
    const saved = localStorage.getItem('recommendations_freshness');
    return saved ? saved : new Date().toLocaleString('en-US');
  });

  const [activeTab, setActiveTab] = useState('all');
  const [isGenerating, setIsGenerating] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Sync dismissed list to localStorage
  useEffect(() => {
    localStorage.setItem('dismissed_recommendations', JSON.stringify(dismissedIds));
  }, [dismissedIds]);

  // Construct recommendations dynamically based on backend analysis
  const recommendationsList = useMemo(() => {
    const recs = [];

    // 1. priorities
    if (Array.isArray(priorities)) {
      priorities.forEach((p) => {
        if (p.priority_score > 35) {
          recs.push({
            id: `priority-${p.course_id || p.id}`,
            title: `Intensify learning: ${p.course_name}`,
            description: `Priority subject scored at ${p.priority_score.toFixed(0)}/100. Spend about ${p.recommended_weekly_hours?.toFixed(1) || '3'}h on it this week to maximize your chances.`,
            category: 'priority',
            priority: Math.min(5, Math.max(1, Math.ceil(p.priority_score / 20))),
            subjectId: p.course_id,
            subjectName: p.course_name
          });
        }
      });
    }

    // 2. risk alerts
    if (Array.isArray(riskScores)) {
      riskScores.forEach((r) => {
        if (r.risk_level === 'high' || r.risk_level === 'medium') {
          recs.push({
            id: `risk-${r.course_id || r.id}`,
            title: `${r.risk_level === 'high' ? 'High' : 'Medium'} Risk Alert: ${r.course_name || 'Course'}`,
            description: `Subject presenting a significant risk of failure. Focus on practical exercises and targeted revisions for this course.`,
            category: 'alert',
            priority: r.risk_level === 'high' ? 5 : 4,
            subjectId: r.course_id,
            subjectName: r.course_name
          });
        }
      });
    }

    // 3. failed courses
    if (Array.isArray(failedCourses)) {
      failedCourses.forEach((fc) => {
        recs.push({
          id: `failed-${fc.course_id}`,
          title: `Retake required: ${fc.course_name}`,
          description: `This course has been marked as failed (Attempts: ${fc.attempt_count}). ${fc.is_prerequisite_blocker ? `WARNING: Blocker subject preventing validation of: ${fc.blocks_courses?.join(', ') || 'other courses'}.` : ''} Make it a priority to schedule study sessions.`,
          category: 'alert',
          priority: fc.is_prerequisite_blocker ? 5 : 4,
          subjectId: fc.course_id,
          subjectName: fc.course_name
        });
      });
    }

    // 4. ECTS progression
    if (ectsProgression) {
      recs.push({
        id: 'ects-progression-rec',
        title: 'ECTS & Degree Analysis',
        description: `You have validated ${ectsProgression.obtained?.toFixed(1) || '0.0'} ECTS out of a total objective of ${ectsProgression.target || '180'} ECTS (${ectsProgression.percentage?.toFixed(1) || '0.0'}% completed). There are ${ectsProgression.remaining?.toFixed(1) || '0.0'} ECTS remaining.`,
        category: 'analysis',
        priority: 3,
      });
    }

    // 5. upcoming exams countdown
    if (Array.isArray(upcomingExams)) {
      upcomingExams.forEach((ex) => {
        const days = ex.days_until ?? 10;
        if (days <= 7) {
          recs.push({
            id: `exam-upcoming-${ex.id}`,
            title: `Imminent Exam: ${ex.course_name || ex.subject_name}`,
            description: `Your exam is on ${new Date(ex.exam_date).toLocaleDateString('en-US')} (${days} days remaining). Recommended prep: at least ${ex.preparation_time_recommended || '10'}h of study this week.`,
            category: 'priority',
            priority: days <= 2 ? 5 : 4,
            subjectId: ex.subject_id,
            subjectName: ex.course_name || ex.subject_name
          });
        }
      });
    }

    // 6. Generic Suggestions
    recs.push({
      id: 'suggest-spaced-repetition',
      title: 'Suggested Learning Technique',
      description: 'Use the spaced repetition principle to review your study notes at intervals of 1, 3, and 7 days.',
      category: 'suggestion',
      priority: 2
    });

    recs.push({
      id: 'suggest-pomodoro',
      title: 'Focus Time Optimization',
      description: 'Apply the Pomodoro method: 25 minutes of intense study followed by a 5-minute break to rest your brain.',
      category: 'suggestion',
      priority: 2
    });

    // Filter out dismissed ones
    return recs.filter((rec) => !dismissedIds.includes(rec.id));
  }, [priorities, riskScores, failedCourses, ectsProgression, upcomingExams, dismissedIds]);

  const handleDismiss = (id, feedback) => {
    setDismissedIds((prev) => [...prev, id]);
    showToast(`Recommendation hidden (Reason: ${feedback})`);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setToastMessage(null);
    try {
      await recalculateAnalysis();
      // Clear dismissed items to refresh recommendations
      setDismissedIds([]);
      const nowStr = new Date().toLocaleString('en-US');
      setFreshnessTime(nowStr);
      localStorage.setItem('recommendations_freshness', nowStr);
      showToast('Recommendations updated by AI!');
    } catch (err) {
      console.error('Error generating recommendations:', err);
      showToast('Error during generation', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const showToast = (msg, type = 'success') => {
    setToastMessage({ text: msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'priority', label: 'Study Priorities' },
    { id: 'alert', label: 'Risk Alerts' },
    { id: 'suggestion', label: 'Time Management' },
    { id: 'analysis', label: 'Analyses' }
  ];

  const isLoading = loading || isGenerating;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl border shadow-2xl transition-all duration-300 flex items-center gap-2 ${
          toastMessage.type === 'error'
            ? 'bg-red-500/10 border-red-500/20 text-red-300'
            : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
        }`}>
          <span>{toastMessage.type === 'error' ? '❌' : '✨'}</span>
          <span className="text-sm font-semibold">{toastMessage.text}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <span>AI Recommendations</span>
            <Badge variant="cyan">Updated: {freshnessTime}</Badge>
          </h1>
          <p className="text-white/40 text-sm mt-1">
            Personalized recommendations generated by Llama + LoRA tailored to your academic progression.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={handleGenerate}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2" />
              </svg>
              Update AI Advice
            </>
          )}
        </Button>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap items-center gap-2 mb-8 border-b border-white/5 pb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
              activeTab === tab.id
                ? 'bg-violet-600/25 border-violet-500/30 text-violet-200 shadow-glow-sm'
                : 'bg-white/5 border-transparent text-white/60 hover:text-white hover:bg-white/10'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((skeletonIdx) => (
            <Card key={skeletonIdx} className="space-y-4 p-5">
              <div className="flex justify-between items-center">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="h-6 w-3/4 mt-2" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-10 w-full mt-4" />
            </Card>
          ))}
        </div>
      ) : (
        <PriorityList
          recommendations={recommendationsList}
          onDismiss={handleDismiss}
          activeTab={activeTab}
        />
      )}
    </div>
  );
};

export default RecommendationsPage;
