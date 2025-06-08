import React from 'react';
import { formatDistanceToNow } from 'date-fns';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
  league_id?: number;
  team_id?: number;
  player_id?: number;
}

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: number) => void;
  onDelete: (id: number) => void;
  onClick?: (notification: Notification) => void;
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'draft_pick':
    case 'draft_start':
    case 'draft_complete':
      return '🏀';
    case 'roster_add':
    case 'roster_drop':
      return '👥';
    case 'trade_offer':
    case 'trade_accepted':
    case 'trade_rejected':
      return '🔄';
    case 'league_invite':
      return '📧';
    case 'game_start':
      return '🎮';
    case 'weekly_summary':
      return '📊';
    case 'success':
      return '✅';
    case 'warning':
      return '⚠️';
    case 'error':
      return '❌';
    default:
      return 'ℹ️';
  }
};

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'success':
    case 'draft_complete':
    case 'trade_accepted':
      return 'border-green-200 bg-green-50';
    case 'warning':
      return 'border-yellow-200 bg-yellow-50';
    case 'error':
    case 'trade_rejected':
      return 'border-red-200 bg-red-50';
    case 'draft_pick':
    case 'draft_start':
    case 'game_start':
      return 'border-blue-200 bg-blue-50';
    default:
      return 'border-gray-200 bg-gray-50';
  }
};

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete,
  onClick,
}) => {
  const handleClick = () => {
    if (!notification.is_read) {
      onMarkAsRead(notification.id);
    }
    onClick?.(notification);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(notification.id);
  };

  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation();
    onMarkAsRead(notification.id);
  };

  return (
    <div
      className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
        notification.is_read ? 'bg-white border-gray-200' : getNotificationColor(notification.type)
      } ${!notification.is_read ? 'border-l-4 border-l-blue-500' : ''}`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <div className="text-lg">{getNotificationIcon(notification.type)}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h4 className={`text-sm font-medium ${notification.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                {notification.title}
              </h4>
              {!notification.is_read && (
                <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
              )}
            </div>
            <p className={`text-sm mt-1 ${notification.is_read ? 'text-gray-500' : 'text-gray-700'}`}>
              {notification.message}
            </p>
            <p className="text-xs text-gray-400 mt-2">
              {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2 ml-2">
          {!notification.is_read && (
            <button
              onClick={handleMarkAsRead}
              className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
              title="Mark as read"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
          )}
          <button
            onClick={handleDelete}
            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete notification"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};