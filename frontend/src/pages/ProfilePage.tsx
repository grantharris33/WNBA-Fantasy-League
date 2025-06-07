import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, fetchJSON } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

interface UserProfile {
  id: number;
  user_id: number;
  email: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  location?: string;
  timezone: string;
  email_verified: boolean;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  accent_color?: string;
  email_notifications: boolean;
  email_draft_reminders: boolean;
  email_trade_offers: boolean;
  email_league_updates: boolean;
  email_weekly_summary: boolean;
  dashboard_layout: Record<string, unknown>;
  default_league_id?: number;
  show_player_photos: boolean;
  favorite_team_ids: number[];
  profile_visibility: 'public' | 'league_only' | 'private';
  show_email: boolean;
  show_stats: boolean;
}

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme, setTheme, accentColor, setAccentColor } = useTheme();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security'>('profile');
  
  // Form states
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [location, setLocation] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [newEmail, setNewEmail] = useState('');
  const [emailPassword, setEmailPassword] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchProfile();
  }, [user, navigate]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const [profileRes, prefsRes] = await Promise.all([
        api.get('/api/v1/profile'),
        api.get('/api/v1/profile/preferences')
      ]);
      
      setProfile((profileRes as any).data);
      setPreferences((prefsRes as any).data);
      
      // Set form values
      setDisplayName((profileRes as any).data.display_name || '');
      setBio((profileRes as any).data.bio || '');
      setLocation((profileRes as any).data.location || '');
      setTimezone((profileRes as any).data.timezone || 'UTC');
    } catch {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      setSuccessMessage(null);
      
      const response = await api.put('/api/v1/profile', {
        display_name: displayName,
        bio,
        location,
        timezone
      });
      
      setProfile((response as any).data);
      setSuccessMessage('Profile updated successfully');
    } catch (err: unknown) {
      const errorMessage = err && typeof err === 'object' && 'response' in err && err.response && typeof err.response === 'object' && 'data' in err.response && err.response.data && typeof err.response.data === 'object' && 'detail' in err.response.data ? String(err.response.data.detail) : 'Failed to update profile';
      setError(errorMessage);
    }
  };

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      setError(null);
      setSuccessMessage(null);
      
      await api.put('/api/v1/profile/password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      
      setSuccessMessage('Password updated successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      setError('Failed to update password');
    }
  };

  const handleEmailUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setError(null);
      setSuccessMessage(null);
      
      await api.put('/api/v1/profile/email', {
        new_email: newEmail,
        password: emailPassword
      });
      
      setSuccessMessage('Email updated. Please check your inbox to verify the new address.');
      setNewEmail('');
      setEmailPassword('');
    } catch {
      setError('Failed to update email');
    }
  };

  const handlePreferenceUpdate = async (key: string, value: unknown) => {
    try {
      setError(null);
      
      await api.put('/api/v1/profile/preferences', {
        [key]: value
      });
      
      setPreferences(prev => prev ? { ...prev, [key]: value } : null);
    } catch {
      setError('Failed to update preferences');
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      setError(null);
      const formData = new FormData();
      formData.append('file', file);
      
      // FormData will be handled properly by fetchJSON
      const response = await fetchJSON('/api/v1/profile/avatar', {
        method: 'POST',
        body: formData
      });
      
      setProfile((response as any).data);
      setSuccessMessage('Avatar uploaded successfully');
    } catch {
      setError('Failed to upload avatar');
    }
  };

  const handleResendVerification = async () => {
    try {
      setError(null);
      await api.post('/api/v1/profile/resend-verification');
      setSuccessMessage('Verification email sent');
    } catch {
      setError('Failed to send verification email');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">User Profile</h1>
      
      {error && <ErrorMessage message={error} />}
      {successMessage && (
        <div className="mb-4 p-4 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg">
          {successMessage}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-8 border-b dark:border-gray-700">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'profile'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'preferences'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Preferences
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'security'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Security
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && profile && (
        <div className="space-y-8">
          {/* Avatar Section */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Avatar</h2>
            <div className="flex items-center space-x-4">
              <div className="w-24 h-24 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center overflow-hidden">
                {profile.avatar_url ? (
                  <img src={profile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl text-gray-500 dark:text-gray-400">
                    {displayName?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || '?'}
                  </span>
                )}
              </div>
              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                  className="hidden"
                  id="avatar-upload"
                />
                <label
                  htmlFor="avatar-upload"
                  className="cursor-pointer px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Upload New Avatar
                </label>
                {profile.avatar_url && (
                  <button
                    onClick={async () => {
                      try {
                        await api.delete('/api/v1/profile/avatar');
                        fetchProfile();
                        setSuccessMessage('Avatar deleted successfully');
                      } catch {
                        setError('Failed to delete avatar');
                      }
                    }}
                    className="ml-2 px-4 py-2 text-red-600 hover:text-red-700 transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Profile Information */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Profile Information</h2>
            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  placeholder="Your display name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Bio</label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  rows={3}
                  placeholder="Tell us about yourself"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  placeholder="City, State"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                </select>
              </div>
              
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </form>
          </div>

          {/* Email Verification */}
          {!profile.email_verified && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Email Not Verified</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Please verify your email address to access all features.
              </p>
              <button
                onClick={handleResendVerification}
                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
              >
                Resend Verification Email
              </button>
            </div>
          )}
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && preferences && (
        <div className="space-y-8">
          {/* Theme Preferences */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Theme & Appearance</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Theme</label>
                <div className="flex space-x-4">
                  {(['light', 'dark', 'system'] as const).map((t) => (
                    <label key={t} className="flex items-center">
                      <input
                        type="radio"
                        value={t}
                        checked={theme === t}
                        onChange={() => setTheme(t)}
                        className="mr-2"
                      />
                      <span className="capitalize">{t}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Accent Color</label>
                <input
                  type="color"
                  value={accentColor}
                  onChange={(e) => setAccentColor(e.target.value)}
                  className="h-10 w-20"
                />
              </div>
            </div>
          </div>

          {/* Notification Preferences */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Email Notifications</h2>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.email_notifications}
                  onChange={(e) => handlePreferenceUpdate('email_notifications', e.target.checked)}
                  className="mr-3"
                />
                <span>Enable email notifications</span>
              </label>
              
              {preferences.email_notifications && (
                <>
                  <label className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      checked={preferences.email_draft_reminders}
                      onChange={(e) => handlePreferenceUpdate('email_draft_reminders', e.target.checked)}
                      className="mr-3"
                    />
                    <span>Draft reminders</span>
                  </label>
                  
                  <label className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      checked={preferences.email_trade_offers}
                      onChange={(e) => handlePreferenceUpdate('email_trade_offers', e.target.checked)}
                      className="mr-3"
                    />
                    <span>Trade offers</span>
                  </label>
                  
                  <label className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      checked={preferences.email_league_updates}
                      onChange={(e) => handlePreferenceUpdate('email_league_updates', e.target.checked)}
                      className="mr-3"
                    />
                    <span>League updates</span>
                  </label>
                  
                  <label className="flex items-center ml-6">
                    <input
                      type="checkbox"
                      checked={preferences.email_weekly_summary}
                      onChange={(e) => handlePreferenceUpdate('email_weekly_summary', e.target.checked)}
                      className="mr-3"
                    />
                    <span>Weekly summary</span>
                  </label>
                </>
              )}
            </div>
          </div>

          {/* Privacy Settings */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Privacy Settings</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Profile Visibility</label>
                <select
                  value={preferences.profile_visibility}
                  onChange={(e) => handlePreferenceUpdate('profile_visibility', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                >
                  <option value="public">Public</option>
                  <option value="league_only">League Members Only</option>
                  <option value="private">Private</option>
                </select>
              </div>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.show_email}
                  onChange={(e) => handlePreferenceUpdate('show_email', e.target.checked)}
                  className="mr-3"
                />
                <span>Show email address on profile</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.show_stats}
                  onChange={(e) => handlePreferenceUpdate('show_stats', e.target.checked)}
                  className="mr-3"
                />
                <span>Show statistics on profile</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-8">
          {/* Change Password */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Change Password</h2>
            <form onSubmit={handlePasswordUpdate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  minLength={8}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  minLength={8}
                  required
                />
              </div>
              
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Update Password
              </button>
            </form>
          </div>

          {/* Change Email */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Change Email</h2>
            <form onSubmit={handleEmailUpdate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Current Email</label>
                <p className="text-gray-600 dark:text-gray-400">{profile?.email}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">New Email</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Confirm Password</label>
                <input
                  type="password"
                  value={emailPassword}
                  onChange={(e) => setEmailPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700"
                  required
                />
              </div>
              
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Update Email
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;