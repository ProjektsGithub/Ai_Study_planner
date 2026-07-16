import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import PropTypes from 'prop-types';

const NavLink = ({ to, children }) => {
  const { pathname } = useLocation();
  const isActive = pathname === to || (to !== '/' && pathname.startsWith(to));

  return (
    <Link
      to={to}
      className={`nav-link ${isActive ? 'active' : ''}`}
    >
      {children}
    </Link>
  );
};

NavLink.propTypes = {
  to: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

const Header = ({ onNotificationClick, unreadCount = 0, onMenuClick }) => {
  const { user, logout, isAuthenticated, roles } = useAuth();
  const { lang, changeLanguage, t } = useLanguage();
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  const userRole = roles && roles.length > 0 ? roles[0].role_display_name : 'Student';

  return (
    <header
      className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-white/10"
      style={{ boxShadow: '0 1px 0 rgba(0,0,0,0.01), 0 4px 30px rgba(0,0,0,0.015)' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">

          <div className="flex items-center gap-3">
            {/* Hamburger menu button */}
            {isAuthenticated && (
              <button
                type="button"
                onClick={onMenuClick}
                className="p-2.5 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-white/50 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200"
                aria-label="Toggle menu"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
          </div>

          {/* Search Bar - Schoooli Style */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center flex-1 max-w-sm ml-6 mr-auto">
              <div className="relative w-full">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-violet-500">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search anything here"
                  className="w-full pl-10 pr-4 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-white/5 border border-transparent dark:border-white/10 rounded-full transition-all duration-300 focus:outline-none focus:bg-white focus:border-violet-500/30 focus:shadow-[0_0_0_3px_rgba(124,58,237,0.08)] placeholder:text-slate-450 dark:placeholder:text-white/20"
                />
              </div>
            </div>
          )}

          {/* Right side */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                {/* Chat Bot Button / Trigger Indicator */}
                <button
                  id="header-chat-btn"
                  className="relative p-2.5 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-white/50 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200"
                  aria-label="Messages"
                  onClick={() => {
                    const chatTrigger = document.getElementById('chat-trigger-btn');
                    if (chatTrigger) chatTrigger.click();
                  }}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </button>

                {/* Notifications */}
                <button
                  id="notifications-btn"
                  onClick={onNotificationClick}
                  className="relative p-2.5 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-white/50 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200"
                  aria-label="Notifications"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {unreadCount > 0 && (
                    <span className="notif-dot absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-space-900" />
                  )}
                </button>

                {/* Language Selector Dropdown next to notifications */}
                <div className="relative">
                  <button
                    onClick={() => setLangMenuOpen(!langMenuOpen)}
                    className="flex items-center gap-1.5 p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-white/50 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200 text-xs font-bold uppercase tracking-wider"
                    aria-label="Change language"
                  >
                    <svg className="w-4 h-4 text-slate-400 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 0 1 9-9" />
                    </svg>
                    <span>{lang}</span>
                    <svg className="w-3 h-3 text-slate-400 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {langMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setLangMenuOpen(false)} />
                      <div className="absolute right-0 top-11 z-20 w-32 bg-white dark:bg-slate-900 border border-slate-100 dark:border-white/10 rounded-xl shadow-lg py-1 animate-slide-up">
                        <button
                          onClick={() => {
                            changeLanguage('en');
                            setLangMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-3.5 py-2 text-xs font-semibold transition-colors ${lang === 'en' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>English</span>
                          {lang === 'en' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                        <button
                          onClick={() => {
                            changeLanguage('fr');
                            setLangMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-3.5 py-2 text-xs font-semibold transition-colors ${lang === 'fr' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>Français</span>
                          {lang === 'fr' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                        <button
                          onClick={() => {
                            changeLanguage('de');
                            setLangMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-3.5 py-2 text-xs font-semibold transition-colors ${lang === 'de' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>Deutsch</span>
                          {lang === 'de' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                      </div>
                    </>
                  )}
                </div>

                {/* User avatar + logout dropdown */}
                <div className="relative flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-white/10">
                  <button
                    onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                    className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 transition-all duration-200"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm">
                      {user?.email?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="hidden sm:flex flex-col text-left leading-none">
                      <span className="text-xs font-bold text-slate-800 dark:text-white">
                        {user?.name || user?.email?.split('@')[0]}
                      </span>
                      <span className="text-[10px] text-slate-400 dark:text-white/40 font-medium mt-0.5">
                        {userRole}
                      </span>
                    </div>
                    <svg className="w-3.5 h-3.5 text-slate-400 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown Menu */}
                  {profileMenuOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setProfileMenuOpen(false)} />
                      <div className="absolute right-0 top-12 z-20 w-52 bg-white dark:bg-slate-900 border border-slate-100 dark:border-white/10 rounded-xl shadow-lg py-1.5 animate-slide-up">
                        <Link
                          to="/profile"
                          onClick={() => setProfileMenuOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                        >
                          {t('nav.my_profile')}
                        </Link>
                        <Link
                          to="/preferences"
                          onClick={() => setProfileMenuOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                        >
                          {t('nav.preferences')}
                        </Link>
                        <div className="h-px bg-slate-100 dark:bg-white/10 my-1" />
                        <div className="px-4 py-1 text-[9px] font-bold text-slate-400 dark:text-white/30 uppercase tracking-wider">
                          Language / Langue
                        </div>
                        <button
                          onClick={() => {
                            changeLanguage('en');
                            setProfileMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-4 py-1.5 text-xs font-semibold transition-colors ${lang === 'en' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>English</span>
                          {lang === 'en' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                        <button
                          onClick={() => {
                            changeLanguage('fr');
                            setProfileMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-4 py-1.5 text-xs font-semibold transition-colors ${lang === 'fr' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>Français</span>
                          {lang === 'fr' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                        <button
                          onClick={() => {
                            changeLanguage('de');
                            setProfileMenuOpen(false);
                          }}
                          className={`w-full text-left flex items-center justify-between px-4 py-1.5 text-xs font-semibold transition-colors ${lang === 'de' ? 'text-violet-600 dark:text-violet-400 bg-violet-50/50 dark:bg-violet-500/5' : 'text-slate-700 dark:text-white/80 hover:bg-slate-50 dark:hover:bg-white/5'}`}
                        >
                          <span>Deutsch</span>
                          {lang === 'de' && <span className="w-1.5 h-1.5 bg-violet-600 dark:bg-violet-400 rounded-full" />}
                        </button>
                        <div className="h-px bg-slate-100 dark:bg-white/10 my-1" />
                        <button
                          onClick={() => {
                            setProfileMenuOpen(false);
                            logout();
                          }}
                          className="w-full text-left flex items-center gap-2.5 px-4 py-2 text-xs font-bold text-red-650 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                        >
                          {t('nav.logout')}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  id="login-link"
                  className="px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-800 rounded-xl hover:bg-slate-100 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  id="register-link"
                  className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-violet-600 to-indigo-500 rounded-xl shadow-glow-sm hover:shadow-glow-violet hover:-translate-y-0.5 transition-all duration-300"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

Header.propTypes = {
  onNotificationClick: PropTypes.func,
  unreadCount: PropTypes.number,
  onMenuClick: PropTypes.func,
};

export default Header;
