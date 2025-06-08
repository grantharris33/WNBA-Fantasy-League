import React, { useState, useEffect, useRef } from 'react';
import { NotificationItem, Notification } from './NotificationItem';
import { NotificationBadge } from './NotificationBadge';

interface NotificationCenterProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: number) => void;
  onMarkAllAsRead: () => void;
  onDelete: (id: number) => void;
  onLoadMore?: () => void;
  isLoading?: boolean;
  hasMore?: boolean;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onDelete,
  onLoadMore,
  isLoading = false,
  hasMore = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const filteredNotifications = showUnreadOnly
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const handleNotificationClick = (notification: Notification) => {
    // Handle navigation based on notification type and associated IDs
    if (notification.league_id) {
      // Navigate to league page
      window.location.href = `/leagues/${notification.league_id}`;
    } else if (notification.team_id) {
      // Navigate to team page
      window.location.href = `/teams/${notification.team_id}`;
    }
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg transition-colors"
        aria-label="Notifications"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unreadCount > 0 && (
          <div className="absolute -top-1 -right-1">
            <NotificationBadge count={unreadCount} />
          </div>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowUnreadOnly(!showUnreadOnly)}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    showUnreadOnly
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {showUnreadOnly ? 'Show All' : 'Unread Only'}
                </button>
                {unreadCount > 0 && (
                  <button
                    onClick={onMarkAllAsRead}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
                  >
                    Mark All Read
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <p className="text-sm">
                  {showUnreadOnly ? 'No unread notifications' : 'No notifications yet'}
                </p>
              </div>
            ) : (
              <div className="p-4 space-y-3">
                {filteredNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={onMarkAsRead}
                    onDelete={onDelete}
                    onClick={handleNotificationClick}
                  />
                ))}
                
                {/* Load More Button */}
                {hasMore && (
                  <div className="pt-2">
                    <button
                      onClick={onLoadMore}
                      disabled={isLoading}
                      className="w-full py-2 text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400 transition-colors"
                    >
                      {isLoading ? 'Loading...' : 'Load More'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <button
              onClick={() => {
                window.location.href = '/notifications';
                setIsOpen(false);
              }}
              className="w-full text-sm text-center text-blue-600 hover:text-blue-800 transition-colors"
            >
              View All Notifications
            </button>
          </div>
        </div>
      )}
    </div>
  );
};