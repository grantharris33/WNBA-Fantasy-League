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
  const [teamName, setTeamName] = useState('');
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

    if (!teamName.trim()) {
      toast.error('Team name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      // First create the league
      const league = await api.leagues.create({
        ...formData,
        draft_date: formData.draft_date || undefined,
      });

      // Then automatically join with the team name
      try {
        await api.leagues.join({
          invite_code: league.invite_code!,
          team_name: teamName.trim()
        });
      } catch (joinError) {
        console.error('Failed to auto-join league:', joinError);
        // Still show success for league creation even if auto-join fails
      }

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
    setTeamName('');
    setCreatedLeague(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {createdLeague ? 'League Created!' : 'Create New League'}
          </h2>

          {createdLeague ? (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-green-600 text-lg">✓</span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-green-800 text-lg">
                      {createdLeague.name}
                    </h3>
                    <p className="text-sm text-green-700">
                      Your league has been created successfully!
                    </p>
                  </div>
                </div>

                <div className="bg-white border border-green-300 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Share this invite code with your friends:
                  </label>
                  <div className="flex items-center gap-3">
                    <code className="flex-1 bg-gray-50 px-4 py-3 rounded-lg text-lg font-mono font-semibold text-gray-900 border">
                      {createdLeague.invite_code}
                    </code>
                    <button
                      onClick={handleCopyInviteCode}
                      className="btn-primary whitespace-nowrap"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleClose}
                  className="flex-1 btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  League Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input"
                  placeholder="Enter league name"
                  required
                />
              </div>

              <div>
                <label htmlFor="teamName" className="block text-sm font-medium text-gray-700 mb-2">
                  Your Team Name *
                </label>
                <input
                  type="text"
                  id="teamName"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  className="input"
                  placeholder="Enter your team name"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  You'll be automatically added to the league as commissioner with this team name.
                </p>
              </div>

              <div>
                <label htmlFor="max_teams" className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Teams
                </label>
                <select
                  id="max_teams"
                  name="max_teams"
                  value={formData.max_teams}
                  onChange={handleInputChange}
                  className="input"
                >
                  {[4, 6, 8, 10, 12].map(num => (
                    <option key={num} value={num}>
                      {num} teams
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="draft_date" className="block text-sm font-medium text-gray-700 mb-2">
                  Draft Date (Optional)
                </label>
                <input
                  type="datetime-local"
                  id="draft_date"
                  name="draft_date"
                  value={formData.draft_date}
                  onChange={handleInputChange}
                  className="input"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 btn-secondary"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Creating...' : 'Create League'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreateLeagueModal;