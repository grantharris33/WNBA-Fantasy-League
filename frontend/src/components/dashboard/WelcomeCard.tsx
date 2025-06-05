import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface WelcomeCardProps {
  hasTeams: boolean;
}

const WelcomeCard: React.FC<WelcomeCardProps> = ({ hasTeams }) => {
  const { user } = useAuth();
  
  if (hasTeams) return null;

  return (
    <div className="card p-8 mb-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
      <div className="flex items-start">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
          <span className="text-2xl">👋</span>
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome to WNBA Fantasy League!
          </h2>
          <p className="text-gray-700 mb-6">
            Get started by joining an existing league or creating your own. Build your dream team
            with the best WNBA players and compete against other managers!
          </p>
          
          <div className="space-y-4">
            <div className="flex items-start">
              <span className="text-lg mr-3">1️⃣</span>
              <div>
                <h3 className="font-semibold text-gray-900">Join or Create a League</h3>
                <p className="text-gray-600 text-sm">
                  Use invite code <code className="bg-gray-100 px-2 py-1 rounded">MVP-DEMO</code> to join the demo league
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <span className="text-lg mr-3">2️⃣</span>
              <div>
                <h3 className="font-semibold text-gray-900">Draft Your Team</h3>
                <p className="text-gray-600 text-sm">
                  Participate in the draft to pick your players
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <span className="text-lg mr-3">3️⃣</span>
              <div>
                <h3 className="font-semibold text-gray-900">Manage Your Roster</h3>
                <p className="text-gray-600 text-sm">
                  Set your lineup, make trades, and climb the standings
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex gap-4 mt-6">
            <Link to="/join" className="btn-primary">
              Join a League
            </Link>
            <button className="btn-secondary" onClick={() => {
              const modal = document.getElementById('create-league-modal');
              if (modal) modal.classList.remove('hidden');
            }}>
              Create League
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeCard;