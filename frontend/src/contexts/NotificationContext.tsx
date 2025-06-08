import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { Notification } from '../components/notifications/NotificationItem';

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: (options?: { limit?: number; offset?: number; unreadOnly?: boolean }) => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: number) => Promise<void>;
  addNotification: (notification: Partial<Notification>) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: React.ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Get auth token from localStorage
  const getAuthToken = () => {
    return localStorage.getItem('token');
  };

  // Fetch notifications from API
  const fetchNotifications = useCallback(async (options: { limit?: number; offset?: number; unreadOnly?: boolean } = {}) => {
    setIsLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        console.warn('No auth token found');
        return;
      }

      const params = new URLSearchParams();
      if (options.limit) params.append('limit', options.limit.toString());
      if (options.offset) params.append('offset', options.offset.toString());
      if (options.unreadOnly) params.append('unread_only', 'true');

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }

      const data = await response.json();
      if (options.offset && options.offset > 0) {
        // Append to existing notifications (pagination)
        setNotifications(prev => [...prev, ...data.notifications]);
      } else {
        // Replace notifications (initial load or refresh)
        setNotifications(data.notifications);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE_URL]);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/unread-count`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.count);
      }
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  }, [API_BASE_URL]);

  // Mark notification as read
  const markAsRead = useCallback(async (id: number) => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/${id}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Update local state
        setNotifications(prev =>
          prev.map(notification =>
            notification.id === id
              ? { ...notification, is_read: true, read_at: new Date().toISOString() }
              : notification
          )
        );
        // Update unread count
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }, [API_BASE_URL]);

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/read-all`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Update local state
        const now = new Date().toISOString();
        setNotifications(prev =>
          prev.map(notification => ({
            ...notification,
            is_read: true,
            read_at: notification.read_at || now,
          }))
        );
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  }, [API_BASE_URL]);

  // Delete notification
  const deleteNotification = useCallback(async (id: number) => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Update local state
        const deletedNotification = notifications.find(n => n.id === id);
        setNotifications(prev => prev.filter(notification => notification.id !== id));
        
        // Update unread count if deleted notification was unread
        if (deletedNotification && !deletedNotification.is_read) {
          setUnreadCount(prev => Math.max(0, prev - 1));
        }
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  }, [API_BASE_URL, notifications]);

  // Add new notification (for real-time updates)
  const addNotification = useCallback((notificationData: Partial<Notification>) => {
    const newNotification: Notification = {
      id: Date.now(), // Temporary ID until real one comes from server
      title: notificationData.title || 'New Notification',
      message: notificationData.message || '',
      type: notificationData.type || 'info',
      is_read: false,
      created_at: new Date().toISOString(),
      ...notificationData,
    } as Notification;

    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);
  }, []);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    
    try {
      const ws = new WebSocket(`${WS_URL}/ws/notifications?token=${token}`);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'notification') {
            addNotification(data.notification);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return () => {
        ws.close();
      };
    } catch (error) {
      console.error('Error setting up WebSocket:', error);
    }
  }, [addNotification]);

  // Polling fallback for unread count
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    // Initial fetch
    fetchUnreadCount();

    // Poll every 30 seconds as fallback
    const interval = setInterval(fetchUnreadCount, 30000);
    
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Initial notification fetch
  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      fetchNotifications({ limit: 20 });
    }
  }, [fetchNotifications]);

  const value = {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    addNotification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};