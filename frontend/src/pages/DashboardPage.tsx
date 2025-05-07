import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import type { LeagueOut } from '../types';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [leagues, setLeagues] = useState<LeagueOut[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch leagues when component mounts
    const fetchLeagues = async () => {
      setIsLoading(true);
      try {
        const data = await api.leagues.getAll();
        setLeagues(data as LeagueOut[]);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load leagues');
        setLeagues([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLeagues();
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">WNBA Fantasy League</h1>

        <div className="flex items-center gap-4">
          <div className="text-gray-600">
            Welcome, <span className="font-semibold">{user?.email}</span>
          </div>
          <button
            onClick={logout}
            className="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Your Leagues</h2>

        {isLoading && (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 text-red-700 p-4 rounded-md">
            {error}
          </div>
        )}

        {!isLoading && !error && leagues.length === 0 && (
          <div className="text-gray-500 text-center py-4">
            You don't have any leagues yet.
          </div>
        )}

        {leagues.length > 0 && (
          <div className="divide-y">
            {leagues.map((league) => (
              <div key={league.id} className="py-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{league.name}</h3>
                    {league.description && (
                      <p className="text-gray-600 text-sm">{league.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <span className={`inline-block px-2 py-1 text-xs rounded
                      ${league.draft_status === 'scheduled' ? 'bg-yellow-100 text-yellow-800' :
                        league.draft_status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                        league.draft_status === 'completed' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'}`}>
                      {league.draft_status.replace('_', ' ')}
                    </span>
                    <a
                      href={`/draft/${league.id}`}
                      className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                    >
                      View
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;