/**
 * SetupProgressBanner
 *
 * Shown on the dashboard when a student has not completed all onboarding steps.
 * Guides them through: Preferences → Courses → Availabilities → Generate Plan
 *
 * Disappears automatically once all 4 steps are done.
 */
import { Link } from 'react-router-dom';

const STEPS = [
  {
    id: 'preferences',
    number: 1,
    title: 'Set your academic profile',
    description: 'Choose your university, program, and semester',
    href: '/preferences',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 'courses',
    number: 2,
    title: 'Select your courses',
    description: 'Mark which courses you are taking this semester',
    href: '/subjects',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    id: 'availabilities',
    number: 3,
    title: 'Set your free time slots',
    description: 'Tell the AI when you are available to study',
    href: '/availabilities',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    id: 'plan',
    number: 4,
    title: 'Generate your AI study plan',
    description: 'Let the AI build your personalized weekly schedule',
    href: '/planner',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
];

/**
 * @param {object} props
 * @param {boolean} props.hasProfile     - student has cursus_id set in preferences
 * @param {boolean} props.hasCourses     - student has at least one enrollment
 * @param {boolean} props.hasAvailabilities - student has at least one availability slot
 * @param {boolean} props.hasPlan        - student has an active study plan
 */
const SetupProgressBanner = ({ hasProfile, hasCourses, hasAvailabilities, hasPlan }) => {
  const stepDone = [hasProfile, hasCourses, hasAvailabilities, hasPlan];
  const completedCount = stepDone.filter(Boolean).length;

  // All done → hide banner
  if (completedCount === 4) return null;

  // Find the first incomplete step for the primary CTA
  const nextStepIndex = stepDone.findIndex((done) => !done);
  const nextStep = STEPS[nextStepIndex];

  return (
    <div className="mb-8 rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-600/10 via-indigo-600/5 to-transparent p-6 relative overflow-hidden">
      {/* Background glow */}
      <div className="pointer-events-none absolute -top-16 -right-16 w-64 h-64 rounded-full bg-violet-600/10 blur-3xl" />

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">🚀</span>
            <h2 className="text-lg font-bold text-white">Get started in 4 steps</h2>
          </div>
          <p className="text-sm text-white/45">
            Complete your setup so the AI can generate a personalized study plan for you.
          </p>
        </div>
        {/* Progress indicator */}
        <div className="flex-shrink-0 text-right">
          <p className="text-2xl font-bold text-white">{completedCount}<span className="text-white/30 text-base font-normal">/4</span></p>
          <p className="text-xs text-white/35 mt-0.5">steps done</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-white/5 rounded-full mb-5 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-violet-500 to-indigo-400 rounded-full transition-all duration-700"
          style={{ width: `${(completedCount / 4) * 100}%` }}
        />
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {STEPS.map((step, idx) => {
          const done = stepDone[idx];
          const isNext = idx === nextStepIndex;

          return (
            <Link
              key={step.id}
              to={step.href}
              id={`setup-step-${step.id}`}
              className={`
                group relative flex flex-col gap-2.5 p-4 rounded-xl border transition-all duration-200
                ${done
                  ? 'border-emerald-500/20 bg-emerald-500/5 cursor-default pointer-events-none'
                  : isNext
                    ? 'border-violet-500/40 bg-violet-500/10 hover:bg-violet-500/15 hover:border-violet-400/60 hover:-translate-y-0.5 shadow-glow-sm'
                    : 'border-white/8 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/15 opacity-60'
                }
              `}
            >
              {/* Step number badge */}
              <div className="flex items-center justify-between">
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                  ${done
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : isNext
                      ? 'bg-violet-500/25 text-violet-300'
                      : 'bg-white/5 text-white/30'
                  }
                `}>
                  {done ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : step.icon}
                </div>
                {isNext && (
                  <span className="text-[10px] font-bold text-violet-300 bg-violet-500/20 px-2 py-0.5 rounded-full border border-violet-500/30">
                    NEXT
                  </span>
                )}
                {done && (
                  <span className="text-[10px] font-bold text-emerald-300">DONE</span>
                )}
              </div>

              <div>
                <p className={`text-xs font-semibold leading-snug ${done ? 'text-emerald-300' : isNext ? 'text-white' : 'text-white/50'}`}>
                  {step.title}
                </p>
                <p className="text-[11px] text-white/30 mt-0.5 leading-snug">{step.description}</p>
              </div>

              {/* Arrow for active step */}
              {isNext && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-violet-400/50 group-hover:text-violet-300 transition-colors">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default SetupProgressBanner;
