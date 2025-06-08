import React, { useState, useEffect } from 'react';
import { WaiverClaim } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface MyWaiverClaimsProps {
  teamId: number;
  onClaimCancelled: () => void;
}

const MyWaiverClaims: React.FC<MyWaiverClaimsProps> = ({
  teamId,
  onClaimCancelled
}) => {
  const [claims, setClaims] = useState<WaiverClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClaims();
  }, [teamId]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/teams/${teamId}/waiver-claims`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch waiver claims');
      }

      const claimsData = await response.json();
      setClaims(claimsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch claims');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelClaim = async (claimId: number) => {
    try {
      setCancelling(claimId);
      
      const response = await fetch(`/api/v1/waiver-claims/${claimId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel claim');
      }

      // Refresh claims and notify parent
      fetchClaims();
      onClaimCancelled();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel claim');
    } finally {
      setCancelling(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'successful':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
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
        onRetry={fetchClaims}
      />
    );
  }

  if (claims.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No waiver claims submitted</p>
        <p className="text-gray-400 text-sm mt-1">
          Submit claims from the Available Players tab
        </p>
      </div>
    );
  }

  const pendingClaims = claims.filter(claim => claim.status === 'pending');
  const processedClaims = claims.filter(claim => claim.status !== 'pending');

  return (
    <div className="space-y-6">
      {/* Pending Claims */}
      {pendingClaims.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Pending Claims ({pendingClaims.length})
          </h3>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-yellow-200">
              <thead className="bg-yellow-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-yellow-800 uppercase tracking-wider">
                    Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-yellow-800 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-yellow-800 uppercase tracking-wider">
                    Drop Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-yellow-800 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-yellow-800 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-yellow-50 divide-y divide-yellow-200">
                {pendingClaims.map((claim) => (
                  <tr key={claim.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {claim.player_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {claim.player_position}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{claim.priority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {claim.drop_player_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(claim.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleCancelClaim(claim.id)}
                        disabled={cancelling === claim.id}
                        className="text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                      >
                        {cancelling === claim.id ? 'Cancelling...' : 'Cancel'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Processed Claims */}
      {processedClaims.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Processed Claims ({processedClaims.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Drop Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processed
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processedClaims.map((claim) => (
                  <tr key={claim.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {claim.player_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {claim.player_position}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{claim.priority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {claim.drop_player_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={getStatusBadge(claim.status)}>
                        {claim.status.charAt(0).toUpperCase() + claim.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {claim.processed_at ? new Date(claim.processed_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyWaiverClaims;