import { useState, useEffect, useMemo } from 'react';
import { useAcademicData } from '../context/AcademicDataContext';
import { useLanguage } from '../context/LanguageContext';
import PriorityList from '../components/recommendations/PriorityList';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Skeleton from '../components/ui/Skeleton';

const RecommendationsPage = () => {
  const {
    subjects,
    priorities,
    riskScores,
    failedCourses,
    ectsProgression,
    upcomingExams,
    recalculateAnalysis,
    fetchAllData,
    loading
  } = useAcademicData();

  const { lang, t, formatEuroDate } = useLanguage();

  const [dismissedIds, setDismissedIds] = useState(() => {
    const saved = localStorage.getItem('dismissed_recommendations');
    return saved ? JSON.parse(saved) : [];
  });

  const [freshnessTime, setFreshnessTime] = useState(() => {
    const saved = localStorage.getItem('recommendations_freshness');
    return saved ? saved : new Date().toLocaleString(lang === 'fr' ? 'fr-FR' : lang === 'de' ? 'de-DE' : 'en-US');
  });

  const [activeTab, setActiveTab] = useState('all');
  const [isGenerating, setIsGenerating] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Sync dismissed list to localStorage
  useEffect(() => {
    localStorage.setItem('dismissed_recommendations', JSON.stringify(dismissedIds));
  }, [dismissedIds]);

  // Construct recommendations dynamically based on enrolled subjects + backend analysis
  const recommendationsList = useMemo(() => {
    const recs = [];

    // 1. Personalized Subject Cards based on Student's Current Enrolled Courses
    if (Array.isArray(subjects) && subjects.length > 0) {
      subjects.forEach((s) => {
        // High priority / High difficulty course card
        if ((s.priority && s.priority >= 4) || (s.difficulty && s.difficulty >= 4)) {
          recs.push({
            id: `subject-priority-${s.id}`,
            title: `🎯 ${s.name}`,
            description: lang === 'fr'
              ? `Matière à forte priorité (${s.priority || 4}/5) et difficulté (${s.difficulty || 4}/5). Allouez au moins ${s.target_weekly_hours || 4}h cette semaine avec une alternance de théorie et d'exercices ciblés.`
              : lang === 'de'
              ? `Fach mit hoher Priorität (${s.priority || 4}/5) und Schwierigkeit (${s.difficulty || 4}/5). Planen Sie mindestens ${s.target_weekly_hours || 4} Std. pro Woche ein.`
              : `High-priority course (${s.priority || 4}/5) and difficulty (${s.difficulty || 4}/5). Allocate at least ${s.target_weekly_hours || 4}h this week with focused exercises.`,
            category: 'priority',
            priority: Math.min(5, Math.max(3, s.priority || 4)),
            subjectId: s.id,
            subjectName: s.name
          });
        }

        // Course with registered weak topics / chapters
        if (s.weak_topics && ((Array.isArray(s.weak_topics) && s.weak_topics.length > 0) || (typeof s.weak_topics === 'string' && s.weak_topics.trim()))) {
          const topicsStr = Array.isArray(s.weak_topics) ? s.weak_topics.join(', ') : s.weak_topics;
          recs.push({
            id: `subject-weak-${s.id}`,
            title: `⚠️ ${s.name}`,
            description: lang === 'fr'
              ? `Notions signalées comme fragiles : ${topicsStr}. Planifiez des séances de révision ciblées et des fiches de synthèse.`
              : lang === 'de'
              ? `Schwierige Themenbereiche: ${topicsStr}. Planen Sie gezielte Wiederholungseinheiten ein.`
              : `Challenging topics identified: ${topicsStr}. Schedule targeted revision sessions.`,
            category: 'alert',
            priority: 4,
            subjectId: s.id,
            subjectName: s.name
          });
        }

        // Course with exam date scheduled
        if (s.exam_date) {
          const examD = new Date(s.exam_date);
          const daysLeft = Math.ceil((examD - new Date()) / (1000 * 60 * 60 * 24));
          const examFormatted = examD.toLocaleDateString(lang === 'fr' ? 'fr-FR' : lang === 'de' ? 'de-DE' : 'en-US');
          recs.push({
            id: `subject-exam-${s.id}`,
            title: `📅 ${s.name}`,
            description: lang === 'fr'
              ? `Examen prévu le ${examFormatted} ${daysLeft > 0 ? `(dans ${daysLeft} jours)` : ''}. ${s.exam_type ? `Format: ${s.exam_type}.` : ''} Priorisez les annales et examens blancs.`
              : lang === 'de'
              ? `Prüfung am ${examFormatted} ${daysLeft > 0 ? `(in ${daysLeft} Tagen)` : ''}. ${s.exam_type ? `Format: ${s.exam_type}.` : ''}`
              : `Exam scheduled on ${examFormatted} ${daysLeft > 0 ? `(in ${daysLeft} days)` : ''}. ${s.exam_type ? `Format: ${s.exam_type}.` : ''}`,
            category: 'priority',
            priority: daysLeft <= 7 ? 5 : 4,
            subjectId: s.id,
            subjectName: s.name
          });
        }

        // General study card per enrolled subject
        recs.push({
          id: `subject-general-${s.id}`,
          title: `📚 ${s.name}`,
          description: lang === 'fr'
            ? `Objectif hebdomadaire conseillé : ${s.target_weekly_hours || 3}h. ECTS : ${s.ects_credits || 3}. Répartissez la charge sur plusieurs sessions de 45 à 90 minutes.`
            : lang === 'de'
            ? `Empfohlenes Wochenziel: ${s.target_weekly_hours || 3} Std. ECTS: ${s.ects_credits || 3}. Verteilen Sie die Einheiten auf 45–90 Min.`
            : `Recommended weekly target: ${s.target_weekly_hours || 3}h. ECTS: ${s.ects_credits || 3}. Split study sessions into 45-90 min blocks.`,
          category: 'suggestion',
          priority: 3,
          subjectId: s.id,
          subjectName: s.name
        });
      });
    }

    // 2. Priority backend score analysis
    if (Array.isArray(priorities)) {
      priorities.forEach((p) => {
        if (p.priority_score > 35) {
          recs.push({
            id: `priority-${p.course_id || p.id}`,
            title: `${p.course_name}`,
            description: lang === 'fr'
              ? `Matière prioritaire avec un score de ${p.priority_score.toFixed(0)}/100. Consacrez environ ${p.recommended_weekly_hours?.toFixed(1) || '3'}h cette semaine.`
              : lang === 'de'
              ? `Prioritätsfach mit einer Bewertung von ${p.priority_score.toFixed(0)}/100. Wöchentliche Empfehlung: ca. ${p.recommended_weekly_hours?.toFixed(1) || '3'} Std.`
              : `High-priority course with score ${p.priority_score.toFixed(0)}/100. Dedicate approx. ${p.recommended_weekly_hours?.toFixed(1) || '3'}h this week.`,
            category: 'priority',
            priority: Math.min(5, Math.max(1, Math.ceil(p.priority_score / 20))),
            subjectId: p.course_id,
            subjectName: p.course_name
          });
        }
      });
    }

    // 3. Risk Alerts backend analysis
    if (Array.isArray(riskScores)) {
      riskScores.forEach((r) => {
        if (r.risk_level === 'high' || r.risk_level === 'medium') {
          recs.push({
            id: `risk-${r.course_id || r.id}`,
            title: `${r.course_name || 'Matière'}`,
            description: lang === 'fr'
              ? `Matière présentant un risque d'échec significatif. Concentrez-vous sur les travaux pratiques et les révisions ciblées.`
              : lang === 'de'
              ? `Fach mit erhöhtem Prüfungsrisiko. Konzentrieren Sie sich auf Übungsaufgaben und gezielte Wiederholung.`
              : `Course with notable risk of failure. Focus on practice problems and targeted review.`,
            category: 'alert',
            priority: r.risk_level === 'high' ? 5 : 4,
            subjectId: r.course_id,
            subjectName: r.course_name
          });
        }
      });
    }

    // 4. Failed Courses (Rattrapages)
    if (Array.isArray(failedCourses)) {
      failedCourses.forEach((fc) => {
        recs.push({
          id: `failed-${fc.course_id}`,
          title: `${fc.course_name}`,
          description: lang === 'fr'
            ? `Cours non validé (Tentatives: ${fc.attempt_count}). ${fc.is_prerequisite_blocker ? `ATTENTION : Matière bloquante empêchant la validation d'autres cours.` : ''} Planifiez des révisions prioritaires.`
            : lang === 'de'
            ? `Nicht bestandener Kurs (Versuche: ${fc.attempt_count}). ${fc.is_prerequisite_blocker ? `WICHTIG: Voraussetzungsfach für Folgemodule.` : ''} Bitte vorrangig wiederholen.`
            : `Course not passed (Attempts: ${fc.attempt_count}). ${fc.is_prerequisite_blocker ? `IMPORTANT: Prerequisite course blocking future subjects.` : ''} Schedule priority revision.`,
          category: 'alert',
          priority: fc.is_prerequisite_blocker ? 5 : 4,
          subjectId: fc.course_id,
          subjectName: fc.course_name
        });
      });
    }

    // 5. ECTS Progression Analysis
    if (ectsProgression) {
      const obtained = ectsProgression.ects_obtained ?? ectsProgression.obtained ?? 0;
      const target = ectsProgression.ects_required ?? ectsProgression.target ?? 180;
      const percentage = ectsProgression.progression_percentage ?? ectsProgression.percentage ?? 0;
      const remaining = ectsProgression.ects_remaining ?? ectsProgression.remaining ?? 0;

      recs.push({
        id: 'ects-progression-rec',
        title: t('progression.graduation_goal'),
        description: lang === 'fr'
          ? `Vous avez validé ${Number(obtained).toFixed(1)} ECTS sur un objectif total de ${Number(target).toFixed(1)} ECTS (${Number(percentage).toFixed(1)}% accomplis). Il reste ${Number(remaining).toFixed(1)} ECTS à valider.`
          : lang === 'de'
          ? `Sie haben ${Number(obtained).toFixed(1)} von ${Number(target).toFixed(1)} ECTS erreicht (${Number(percentage).toFixed(1)}%). Noch ${Number(remaining).toFixed(1)} ECTS erforderlich.`
          : `You have obtained ${Number(obtained).toFixed(1)} of ${Number(target).toFixed(1)} ECTS (${Number(percentage).toFixed(1)}% complete). ${Number(remaining).toFixed(1)} ECTS remaining.`,
        category: 'analysis',
        priority: 3,
      });
    }

    // 6. Upcoming Exams Countdown
    if (Array.isArray(upcomingExams)) {
      upcomingExams.forEach((ex) => {
        const days = ex.days_until ?? 10;
        if (days <= 7) {
          const exDateStr = new Date(ex.exam_date).toLocaleDateString(lang === 'fr' ? 'fr-FR' : lang === 'de' ? 'de-DE' : 'en-US');
          recs.push({
            id: `exam-upcoming-${ex.id}`,
            title: `${ex.course_name || ex.subject_name}`,
            description: lang === 'fr'
              ? `Épreuve le ${exDateStr} (dans ${days} jours). Préparation conseillée : au moins ${ex.preparation_time_recommended || '10'}h cette semaine.`
              : lang === 'de'
              ? `Prüfung am ${exDateStr} (in ${days} Tagen). Empfohlene Vorbereitungszeit: mind. ${ex.preparation_time_recommended || '10'} Std.`
              : `Exam on ${exDateStr} (in ${days} days). Recommended study volume: at least ${ex.preparation_time_recommended || '10'}h this week.`,
            category: 'priority',
            priority: days <= 2 ? 5 : 4,
            subjectId: ex.subject_id,
            subjectName: ex.course_name || ex.subject_name
          });
        }
      });
    }

    // 7. General Pedagogical Suggestions
    recs.push({
      id: 'suggest-spaced-repetition',
      title: lang === 'fr' ? 'Technique : Répétition Espacée' : lang === 'de' ? 'Methode: Spaced Repetition' : 'Study Tip: Spaced Repetition',
      description: lang === 'fr'
        ? 'Revoyez vos fiches de cours à des intervalles de 1, 3 et 7 jours pour ancrer les connaissances durablement.'
        : lang === 'de'
        ? 'Wiederholen Sie Ihre Lerninhalte in Intervallen von 1, 3 und 7 Tagen für langfristiges Behalten.'
        : 'Review summary sheets at intervals of 1, 3, and 7 days to reinforce long-term retention.',
      category: 'suggestion',
      priority: 2
    });

    recs.push({
      id: 'suggest-pomodoro',
      title: lang === 'fr' ? 'Concentration : Méthode Pomodoro' : lang === 'de' ? 'Konzentration: Pomodoro-Technik' : 'Focus: Pomodoro Technique',
      description: lang === 'fr'
        ? 'Appliquez des sessions de 25 minutes de travail intense suivies de 5 minutes de pause pour maintenir une bonne énergie.'
        : lang === 'de'
        ? 'Arbeiten Sie 25 Minuten hochkonzentriert, gefolgt von 5 Minuten Pause für optimale geistige Frische.'
        : 'Use 25-minute deep work sessions followed by 5-minute short breaks to maintain high focus.',
      category: 'suggestion',
      priority: 2
    });

    // Deduplicate by ID and filter out dismissed ones
    const seen = new Set();
    const uniqueRecs = [];
    for (const rec of recs) {
      if (!seen.has(rec.id) && !dismissedIds.includes(rec.id)) {
        seen.add(rec.id);
        uniqueRecs.push(rec);
      }
    }

    return uniqueRecs;
  }, [subjects, priorities, riskScores, failedCourses, ectsProgression, upcomingExams, dismissedIds, lang, t]);

  const handleDismiss = (id, feedback) => {
    setDismissedIds((prev) => [...prev, id]);
    showToast(`${t('recommendations.toast_dismissed')} (${feedback})`);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setToastMessage(null);
    try {
      if (recalculateAnalysis) {
        await recalculateAnalysis();
      }
      if (fetchAllData) {
        await fetchAllData();
      }
      // Reset dismissed items to refresh recommendations
      setDismissedIds([]);
      const nowStr = new Date().toLocaleString(lang === 'fr' ? 'fr-FR' : lang === 'de' ? 'de-DE' : 'en-US');
      setFreshnessTime(nowStr);
      localStorage.setItem('recommendations_freshness', nowStr);
      showToast(t('recommendations.toast_updated'));
    } catch (err) {
      console.error('Error generating recommendations:', err);
      showToast(t('recommendations.toast_error'), 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const showToast = (msg, type = 'success') => {
    setToastMessage({ text: msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const tabs = [
    { id: 'all', label: t('recommendations.tab.all') },
    { id: 'priority', label: t('recommendations.tab.priority') },
    { id: 'alert', label: t('recommendations.tab.alert') },
    { id: 'suggestion', label: t('recommendations.tab.suggestion') },
    { id: 'analysis', label: t('recommendations.tab.analysis') }
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
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <span>{t('recommendations.title')}</span>
            <Badge variant="cyan">{t('recommendations.updated_at')}: {freshnessTime}</Badge>
          </h1>
          <p className="text-slate-500 dark:text-white/40 text-sm mt-1">
            {t('recommendations.subtitle')}
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
              {t('recommendations.calculating')}
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2" />
              </svg>
              {t('recommendations.refresh_btn')}
            </>
          )}
        </Button>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap items-center gap-2 mb-8 border-b border-slate-200 dark:border-white/5 pb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
              activeTab === tab.id
                ? 'bg-violet-600 text-white border-violet-500 shadow-lg'
                : 'bg-slate-100 dark:bg-white/5 border-transparent text-slate-600 dark:text-white/60 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/10'
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
