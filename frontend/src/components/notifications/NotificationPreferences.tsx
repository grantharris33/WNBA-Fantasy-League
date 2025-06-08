import React, { useState } from 'react';

interface NotificationPreferences {
  draft_picks: boolean;
  roster_moves: boolean;
  trade_offers: boolean;
  game_updates: boolean;
  weekly_summaries: boolean;
  league_announcements: boolean;
  email_notifications: boolean;
}

interface NotificationPreferencesProps {
  preferences: NotificationPreferences;
  onSave: (preferences: NotificationPreferences) => void;
  isLoading?: boolean;
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  preferences,
  onSave,
  isLoading = false,
}) => {
  const [localPreferences, setLocalPreferences] = useState<NotificationPreferences>(preferences);
  const [hasChanges, setHasChanges] = useState(false);

  const handleToggle = (key: keyof NotificationPreferences) => {
    const newPreferences = {
      ...localPreferences,
      [key]: !localPreferences[key],
    };
    setLocalPreferences(newPreferences);
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(localPreferences);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalPreferences(preferences);
    setHasChanges(false);
  };

  const preferenceOptions = [
    {
      key: 'draft_picks' as const,
      label: 'Draft Picks',
      description: 'Get notified when picks are made in your league drafts',
    },
    {
      key: 'roster_moves' as const,
      label: 'Roster Moves',
      description: 'Get notified about player additions and drops',
    },
    {
      key: 'trade_offers' as const,
      label: 'Trade Offers',
      description: 'Get notified about trade proposals and responses',
    },
    {
      key: 'game_updates' as const,
      label: 'Game Updates',
      description: 'Get notified when games start and final scores are available',
    },
    {
      key: 'weekly_summaries' as const,
      label: 'Weekly Summaries',
      description: 'Get weekly performance summaries and league standings',
    },
    {
      key: 'league_announcements' as const,
      label: 'League Announcements',
      description: 'Get notified about league settings changes and announcements',
    },
    {
      key: 'email_notifications' as const,
      label: 'Email Notifications',
      description: 'Receive important notifications via email',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Notification Preferences</h3>
        <p className="text-sm text-gray-600 mt-1">
          Choose which notifications you want to receive
        </p>
      </div>

      <div className="p-6 space-y-6">
        {preferenceOptions.map((option) => (
          <div key={option.key} className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id={option.key}
                type="checkbox"
                checked={localPreferences[option.key]}
                onChange={() => handleToggle(option.key)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            <div className="ml-3">
              <label htmlFor={option.key} className="text-sm font-medium text-gray-900 cursor-pointer">
                {option.label}
              </label>
              <p className="text-sm text-gray-500">{option.description}</p>
            </div>
          </div>
        ))}
      </div>

      {hasChanges && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      )}
    </div>
  );
};