import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../lib/api';
import type { JoinLeagueRequest, UserTeam } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';

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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Join a League
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter the invite code provided by your league commissioner
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="invite_code" className="block text-sm font-medium text-gray-700 mb-1">
                Invite Code *
              </label>
              <input
                id="invite_code"
                name="invite_code"
                type="text"
                value={formData.invite_code}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center font-mono text-lg"
                placeholder="Enter invite code"
                required
              />
            </div>

            <div>
              <label htmlFor="team_name" className="block text-sm font-medium text-gray-700 mb-1">
                Team Name *
              </label>
              <input
                id="team_name"
                name="team_name"
                type="text"
                value={formData.team_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your team name"
                required
              />
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 py-2 px-4 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center">
                  <LoadingSpinner />
                  <span className="ml-2">Joining...</span>
                </div>
              ) : (
                'Join League'
              )}
            </button>
          </div>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">
                Don't have an invite code?
              </span>
            </div>
          </div>

          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-blue-600 hover:text-blue-500 text-sm font-medium"
            >
              Create your own league instead
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinLeaguePage;