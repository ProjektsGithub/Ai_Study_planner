import { Link, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

// Icons definitions
const HomeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const BookOpenIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const LightbulbIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const PreferencesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
  </svg>
);

const CalendarDaysIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const LogoutIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

const menuGroups = [
  {
    titleKey: 'nav.group.overview',
    items: [
      { path: '/dashboard', labelKey: 'nav.dashboard', icon: <HomeIcon /> }
    ]
  },
  {
    titleKey: 'nav.group.planning',
    items: [
      { path: '/ai-plan', labelKey: 'nav.create_plan', icon: <SparklesIcon /> },
      { path: '/planner', labelKey: 'nav.my_study_plans', icon: <CalendarIcon /> },
      { path: '/subjects', labelKey: 'nav.manage_courses', icon: <BookOpenIcon /> }
    ]
  },
  {
    titleKey: 'nav.group.settings',
    items: [
      { path: '/availabilities', labelKey: 'nav.availabilities', icon: <ClockIcon /> },
      { path: '/preferences', labelKey: 'nav.preferences', icon: <PreferencesIcon /> },
      { path: '/constraints', labelKey: 'nav.off_days', icon: <CalendarDaysIcon /> }
    ]
  },
  {
    titleKey: 'nav.group.account',
    items: [
      { path: '/profile', labelKey: 'nav.my_profile', icon: <UserIcon /> },
      { path: '/recommendations', labelKey: 'nav.recommendations', icon: <LightbulbIcon /> },
      { path: 'logout', labelKey: 'nav.logout', icon: <LogoutIcon />, action: true }
    ]
  }
];

const Sidebar = ({ isOpen, onClose }) => {
  const { pathname } = useLocation();
  const { logout } = useAuth();
  const { t } = useLanguage();

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-white/10
        transition-transform duration-300 transform
        md:translate-x-0 md:static md:h-screen flex flex-col overflow-y-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}
    >
      <div className="flex-1 flex flex-col justify-between py-6 px-4">
        <div>
          {/* Logo Area */}
          <div className="flex items-center gap-3 px-4 mb-6">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center shadow-glow-sm">
              <span className="text-lg text-white font-bold">✦</span>
            </div>
          <div className="flex flex-col leading-none">
              <span className="text-base font-bold text-violet-600 dark:text-white tracking-tight">STUDYPLAN AI</span>
              <span className="text-[9px] text-slate-400 dark:text-white/40 font-medium tracking-tight mt-0.5">{t('nav.logo_subtitle')}</span>
            </div>
          </div>
 
          <nav className="space-y-4">
            {menuGroups.map((group) => (
              <div key={group.titleKey} className="space-y-1">
                <div className="text-[10px] font-bold text-slate-400 dark:text-white/30 uppercase tracking-widest px-4 mb-1">
                  {t(group.titleKey)}
                </div>
                {group.items.map((item) => {
                  const isActive = !item.action && (pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path)));
                  
                  if (item.action && item.path === 'logout') {
                    return (
                      <button
                        key={item.labelKey}
                        onClick={() => {
                          logout();
                          onClose();
                        }}
                        className="w-full flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 border border-transparent text-slate-600 hover:text-slate-900 dark:text-white/60 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/5"
                      >
                        <span className="text-slate-400 dark:text-white/40">
                          {item.icon}
                        </span>
                        <span>{t(item.labelKey)}</span>
                      </button>
                    );
                  }
 
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={`
                        flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 border
                        ${isActive
                          ? 'bg-violet-50 dark:bg-violet-600/20 text-violet-700 dark:text-violet-200 border-violet-100 dark:border-violet-500/20'
                          : 'text-slate-600 hover:text-slate-900 dark:text-white/60 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/5 border-transparent'}
                      `}
                    >
                      <span className={isActive ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400 dark:text-white/40'}>
                        {item.icon}
                      </span>
                      <span>{t(item.labelKey)}</span>
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        {/* Tip Box at bottom */}
        <div className="mt-auto pt-6 px-2">
          <div className="relative overflow-hidden rounded-2xl border border-violet-100 bg-violet-50/50 p-4 dark:border-violet-500/10 dark:bg-violet-900/5">
            <div className="absolute -right-6 -top-6 w-16 h-16 rounded-full bg-violet-500/5 blur-lg pointer-events-none" />
            
            <div className="relative z-10 flex items-start gap-2.5">
              <span className="text-xl leading-none">💡</span>
              <div className="flex-1">
                <p className="text-xs font-bold text-slate-800 dark:text-violet-200">{t('study_tip.title')}</p>
                <p className="text-[10px] text-slate-500 dark:text-white/50 mt-1 font-medium leading-relaxed">
                  {t('study_tip.content')}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

Sidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default Sidebar;
