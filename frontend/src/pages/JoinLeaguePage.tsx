import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import type { JoinLeagueRequest, UserTeam } from '../types';

const JoinLeaguePage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<JoinLeagueRequest>({
    invite_code: '',
    team_name: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.invite_code.trim()) {
      toast.error('Invite code is required');
      return;
    }

    if (!formData.team_name.trim()) {
      toast.error('Team name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const team: UserTeam = await api.leagues.join(formData);
      toast.success(`Successfully joined league with team "${team.name}"!`);
      navigate('/');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to join league');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="card p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🏀</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Join a League
            </h2>
            <p className="text-gray-600">
              Enter the invite code provided by your league commissioner
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="invite_code" className="block text-sm font-medium text-gray-700 mb-2">
                Invite Code *
              </label>
              <input
                id="invite_code"
                name="invite_code"
                type="text"
                value={formData.invite_code}
                onChange={handleInputChange}
                className="input text-center font-mono text-lg"
                placeholder="LEAGUE-XXXX-XXXX"
                required
              />
            </div>

            <div>
              <label htmlFor="team_name" className="block text-sm font-medium text-gray-700 mb-2">
                Team Name *
              </label>
              <input
                id="team_name"
                name="team_name"
                type="text"
                value={formData.team_name}
                onChange={handleInputChange}
                className="input"
                placeholder="Enter your team name"
                required
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => navigate('/')}
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
                {isSubmitting ? 'Joining...' : 'Join League'}
              </button>
            </div>
          </form>

          {/* Divider */}
          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Don't have an invite code?
                </span>
              </div>
            </div>

            <div className="mt-6 text-center">
              <button
                onClick={() => navigate('/')}
                className="text-blue-600 hover:text-blue-500 text-sm font-medium transition-colors"
              >
                Create your own league instead
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinLeaguePage;