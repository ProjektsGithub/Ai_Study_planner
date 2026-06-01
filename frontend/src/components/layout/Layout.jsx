import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Header from './Header';
import Footer from './Footer';
import NotificationPanel from '../NotificationPanel';
import apiClient from '../../api/client';

const Layout = ({ children }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

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
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header 
        onNotificationClick={handleNotificationClick}
        unreadCount={unreadCount}
      />
      
      <main className="flex-1">
        {children}
      </main>
      
      <Footer />
      
      <NotificationPanel 
        isOpen={showNotifications}
        onClose={handleCloseNotifications}
      />
    </div>
  );
};

Layout.propTypes = {
  children: PropTypes.node.isRequired
};

export default Layout;
