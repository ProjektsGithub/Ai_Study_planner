import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header
      className="sticky top-0 z-50 bg-white dark:bg-slate-900/95 border-b border-slate-200 dark:border-white/10"
      style={{ boxShadow: '0 1px 0 rgba(0,0,0,0.02), 0 4px 20px rgba(0,0,0,0.05)' }}
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

          {/* Right side */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
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

                {/* User avatar + logout */}
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-white/10">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-glow-sm">
                    {user?.email?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <button
                    id="logout-btn"
                    onClick={logout}
                    className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/8 transition-all duration-200"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Logout
                  </button>
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
