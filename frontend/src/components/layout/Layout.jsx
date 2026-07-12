import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import PropTypes from 'prop-types';
import Header from './Header';
import Footer from './Footer';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import Breadcrumbs from './Breadcrumbs';
import NotificationPanel from '../NotificationPanel';
import ChatBot from '../ChatBot';
import apiClient from '../../api/client';
import { useGamification } from '../../context/GamificationContext';
import CelebrationAnimation from '../gamification/CelebrationAnimation';

const Layout = ({ children }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { activeCelebration, clearCelebration } = useGamification();

  useEffect(() => {
    loadUnreadCount();
    
    // Poll for unread count every 30 seconds
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const response = await apiClient.get('/api/v1/notifications/unread-count');
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };

  const handleNotificationClick = () => {
    setShowNotifications(!showNotifications);
  };

  const handleCloseNotifications = () => {
    setShowNotifications(false);
    // Reload unread count after closing
    loadUnreadCount();
  };

  return (
    <div className="min-h-screen flex flex-col pb-16 md:pb-0" style={{ background: 'var(--color-bg-primary)' }}>
      <div className="flex flex-1 relative overflow-hidden h-screen">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <div className="flex flex-col flex-1 overflow-hidden">
          <Header 
            onNotificationClick={handleNotificationClick}
            unreadCount={unreadCount}
            onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          />
          
          <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6 w-full">
            <Breadcrumbs />
            {/* Support both: legacy children prop and nested route Outlet */}
            {children ?? <Outlet />}
          </main>
        </div>
      </div>
      
      <BottomNav />
      <Footer className="hidden md:block" />
      
      <NotificationPanel 
        isOpen={showNotifications}
        onClose={handleCloseNotifications}
      />

      {activeCelebration && (
        <CelebrationAnimation
          trigger={activeCelebration.type}
          message={activeCelebration.message}
          onClose={clearCelebration}
        />
      )}

      {/* AI Chatbot — floating bubble bottom-right */}
      <ChatBot />
    </div>
  );
};

Layout.propTypes = {
  children: PropTypes.node,
};

export default Layout;
