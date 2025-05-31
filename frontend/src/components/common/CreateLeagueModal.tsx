import React, { useState } from 'react';
import { toast } from 'react-toastify';
import api from '../../lib/api';
import type { LeagueCreate, LeagueOut } from '../../types';

interface CreateLeagueModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLeagueCreated: (league: LeagueOut) => void;
}

const CreateLeagueModal: React.FC<CreateLeagueModalProps> = ({
  isOpen,
  onClose,
  onLeagueCreated,
}) => {
  const [formData, setFormData] = useState<LeagueCreate>({
    name: '',
    max_teams: 8,
    draft_date: '',
    settings: {},
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdLeague, setCreatedLeague] = useState<LeagueOut | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'max_teams' ? parseInt(value, 10) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('League name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const league = await api.leagues.create({
        ...formData,
        draft_date: formData.draft_date || undefined,
      });

      setCreatedLeague(league);
      onLeagueCreated(league);
      toast.success('League created successfully!');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create league');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyInviteCode = async () => {
    if (createdLeague?.invite_code) {
      try {
        await navigator.clipboard.writeText(createdLeague.invite_code);
        toast.success('Invite code copied to clipboard!');
      } catch {
        toast.error('Failed to copy invite code');
      }
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      max_teams: 8,
      draft_date: '',
      settings: {},
    });
    setCreatedLeague(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-2xl font-bold mb-4">
          {createdLeague ? 'League Created!' : 'Create New League'}
        </h2>

        {createdLeague ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2">
                {createdLeague.name}
              </h3>
              <p className="text-sm text-green-700 mb-3">
                Your league has been created! Share the invite code below with your friends.
              </p>

              <div className="bg-white border border-green-300 rounded p-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Invite Code
                </label>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 bg-gray-100 px-3 py-2 rounded text-lg font-mono">
                    {createdLeague.invite_code}
                  </code>
                  <button
                    onClick={handleCopyInviteCode}
                    className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleClose}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                League Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter league name"
                required
              />
            </div>

            <div>
              <label htmlFor="max_teams" className="block text-sm font-medium text-gray-700 mb-1">
                Maximum Teams
              </label>
              <select
                id="max_teams"
                name="max_teams"
                value={formData.max_teams}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[4, 6, 8, 10, 12].map(num => (
                  <option key={num} value={num}>
                    {num} teams
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="draft_date" className="block text-sm font-medium text-gray-700 mb-1">
                Draft Date (Optional)
              </label>
              <input
                type="datetime-local"
                id="draft_date"
                name="draft_date"
                value={formData.draft_date}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Creating...' : 'Create League'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default CreateLeagueModal;