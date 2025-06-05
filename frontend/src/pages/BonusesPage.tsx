import React from 'react';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import WeeklyBonusWinners from '../components/dashboard/WeeklyBonusWinners';

const BonusesPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mr-4"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-1" />
              Back to Dashboard
            </button>
          </div>

          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Weekly Bonus Winners</h1>
            <p className="text-gray-600">See which players earned weekly performance bonuses</p>
          </div>
        </div>

        {/* Weekly Bonus Winners Component */}
        <WeeklyBonusWinners showWeekSelector={true} />
      </div>
    </div>
  );
};

export default BonusesPage;