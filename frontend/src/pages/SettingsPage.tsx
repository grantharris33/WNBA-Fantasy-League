import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: false,
    gameUpdates: true,
    draftReminders: true,
    weeklyRecap: true,
    tradeOffers: true
  });

  const [privacy, setPrivacy] = useState({
    profileVisibility: 'league-members',
    teamNameVisibility: 'public',
    statisticsVisibility: 'public'
  });

  const [preferences, setPreferences] = useState({
    theme: 'light',
    timezone: 'America/New_York',
    language: 'en',
    defaultView: 'dashboard'
  });

  const handleNotificationChange = (key: string, value: boolean) => {
    setNotifications(prev => ({ ...prev, [key]: value }));
  };

  const handlePrivacyChange = (key: string, value: string) => {
    setPrivacy(prev => ({ ...prev, [key]: value }));
  };

  const handlePreferencesChange = (key: string, value: string) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveSettings = () => {
    // TODO: Implement settings save functionality
    console.log('Saving settings:', { notifications, privacy, preferences });
    alert('Settings saved successfully!');
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold leading-tight text-[#0d141c]">Settings</h1>
          <p className="text-slate-500 text-sm font-normal leading-normal mt-2">
            Manage your account preferences and privacy settings
          </p>
        </div>

        {/* Account Information */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Account Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                <input
                  type="text"
                  value={user?.email || 'Not available'}
                  disabled
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">User ID</label>
                <input
                  type="text"
                  value={user?.id?.toString() || 'Not available'}
                  disabled
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Display Name</label>
                <input
                  type="text"
                  placeholder="Enter your display name"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Bio</label>
                <textarea
                  placeholder="Tell others about yourself"
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Notification Preferences */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Notification Preferences</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">Email Notifications</h3>
                  <p className="text-sm text-slate-600">Receive notifications via email</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.email}
                    onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0c7ff2]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0c7ff2]"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">Game Updates</h3>
                  <p className="text-sm text-slate-600">Get notified about game results and player performances</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.gameUpdates}
                    onChange={(e) => handleNotificationChange('gameUpdates', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0c7ff2]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0c7ff2]"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">Draft Reminders</h3>
                  <p className="text-sm text-slate-600">Get reminded about upcoming drafts</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.draftReminders}
                    onChange={(e) => handleNotificationChange('draftReminders', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0c7ff2]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0c7ff2]"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">Weekly Recap</h3>
                  <p className="text-sm text-slate-600">Receive weekly performance summaries</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.weeklyRecap}
                    onChange={(e) => handleNotificationChange('weeklyRecap', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0c7ff2]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0c7ff2]"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-slate-900">Trade Offers</h3>
                  <p className="text-sm text-slate-600">Get notified about trade proposals</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.tradeOffers}
                    onChange={(e) => handleNotificationChange('tradeOffers', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#0c7ff2]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0c7ff2]"></div>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Privacy Settings */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Privacy Settings</h2>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Profile Visibility</label>
                <select
                  value={privacy.profileVisibility}
                  onChange={(e) => handlePrivacyChange('profileVisibility', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="public">Public - Anyone can see</option>
                  <option value="league-members">League Members Only</option>
                  <option value="private">Private - Only me</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Team Name Visibility</label>
                <select
                  value={privacy.teamNameVisibility}
                  onChange={(e) => handlePrivacyChange('teamNameVisibility', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="public">Public</option>
                  <option value="league-members">League Members Only</option>
                  <option value="private">Private</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Statistics Visibility</label>
                <select
                  value={privacy.statisticsVisibility}
                  onChange={(e) => handlePrivacyChange('statisticsVisibility', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="public">Public</option>
                  <option value="league-members">League Members Only</option>
                  <option value="private">Private</option>
                </select>
              </div>
            </div>
          </div>
        </section>

        {/* App Preferences */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">App Preferences</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Theme</label>
                <select
                  value={preferences.theme}
                  onChange={(e) => handlePreferencesChange('theme', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto (System)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Timezone</label>
                <select
                  value={preferences.timezone}
                  onChange={(e) => handlePreferencesChange('timezone', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Default View</label>
                <select
                  value={preferences.defaultView}
                  onChange={(e) => handlePreferencesChange('defaultView', e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0c7ff2] focus:border-[#0c7ff2]"
                >
                  <option value="dashboard">Dashboard</option>
                  <option value="my-teams">My Teams</option>
                  <option value="leagues">Leagues</option>
                  <option value="players">Players</option>
                </select>
              </div>
            </div>
          </div>
        </section>

        {/* Danger Zone */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-red-200">
            <h2 className="text-xl font-bold text-red-600 mb-4">Danger Zone</h2>
            <div className="space-y-4">
              <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                <h3 className="font-medium text-red-800 mb-2">Delete Account</h3>
                <p className="text-sm text-red-600 mb-3">
                  Permanently delete your account and all associated data. This action cannot be undone.
                </p>
                <button className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors">
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Save Settings */}
        <div className="flex justify-end space-x-3">
          <button 
            onClick={() => navigate('/dashboard')}
            className="px-6 py-2 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSaveSettings}
            className="px-6 py-2 bg-[#0c7ff2] text-white font-medium rounded-lg hover:bg-[#0a6bc8] transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default SettingsPage;