import React, { useState, useEffect } from 'react';
import { WaiverPlayer } from '../../types';
import WaiverPlayerList from './WaiverPlayerList';
import MyWaiverClaims from './MyWaiverClaims';
import WaiverCountdown from './WaiverCountdown';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface WaiverWireProps {
  leagueId: number;
  teamId: number;
  onError?: (error: string) => void;
}

const WaiverWire: React.FC<WaiverWireProps> = ({
  leagueId,
  teamId,
  onError
}) => {
  const [waiverPlayers, setWaiverPlayers] = useState<WaiverPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'available' | 'claims'>('available');

  useEffect(() => {
    fetchWaiverPlayers();
  }, [leagueId]);

  const fetchWaiverPlayers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/leagues/${leagueId}/waivers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch waiver wire players');
      }

      const players = await response.json();
      setWaiverPlayers(players);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClaimSubmitted = () => {
    // Refresh the waiver wire when a claim is submitted
    fetchWaiverPlayers();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage 
        message={error}
        onRetry={fetchWaiverPlayers}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with countdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Waiver Wire</h2>
          <WaiverCountdown />
        </div>
        
        <p className="text-gray-600">
          Players dropped by teams enter the waiver wire for a set period. 
          Submit claims with priority rankings to acquire players when waivers process.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('available')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'available'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Available Players ({waiverPlayers.length})
            </button>
            <button
              onClick={() => setActiveTab('claims')}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === 'claims'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Claims
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'available' ? (
            <WaiverPlayerList
              players={waiverPlayers}
              teamId={teamId}
              onClaimSubmitted={handleClaimSubmitted}
            />
          ) : (
            <MyWaiverClaims
              teamId={teamId}
              onClaimCancelled={handleClaimSubmitted}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default WaiverWire;