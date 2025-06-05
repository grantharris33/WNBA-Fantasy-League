import React, { useState, useEffect } from 'react';
import { TrophyIcon, CalendarIcon } from '@heroicons/react/24/outline';
import api from '../../lib/api';
import type { TeamScoreData, BonusDetail } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

interface WeeklyBonusWinnersProps {
  title?: string;
  showWeekSelector?: boolean;
}

interface BonusWinner extends BonusDetail {
  team_id: number;
  team_name: string;
}

const BONUS_CATEGORIES = {
  'top_scorer': {
    label: 'Top Scorer',
    icon: '🏀',
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    description: 'Highest points scored this week'
  },
  'top_rebounder': {
    label: 'Top Rebounder',
    icon: '💪',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    description: 'Most rebounds collected this week'
  },
  'top_playmaker': {
    label: 'Top Playmaker',
    icon: '🎯',
    color: 'bg-green-100 text-green-800 border-green-200',
    description: 'Most assists distributed this week'
  },
  'defensive_beast': {
    label: 'Defensive Beast',
    icon: '🛡️',
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    description: 'Most steals + blocks combined this week'
  },
  'efficiency_award': {
    label: 'Efficiency Award',
    icon: '📊',
    color: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    description: 'Best field goal percentage (≥3 games)'
  },
  'double_double_streak': {
    label: 'Double-Double Streak',
    icon: '⚡',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    description: '2+ double-doubles in a week'
  },
  'triple_double': {
    label: 'Triple-Double',
    icon: '👑',
    color: 'bg-red-100 text-red-800 border-red-200',
    description: 'Achieved a triple-double'
  }
};

const WeeklyBonusWinners: React.FC<WeeklyBonusWinnersProps> = ({
  title = "Weekly Bonus Winners",
  showWeekSelector = false
}) => {
  const [bonusWinners, setBonusWinners] = useState<BonusWinner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentWeek] = useState(1); // TODO: Get from API or state management

  useEffect(() => {
    fetchBonusWinners();
  }, [currentWeek]);

  const fetchBonusWinners = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get current scores which include bonus data
      const scores: TeamScoreData[] = await api.scores.getCurrent();

      // Extract all bonuses with team information
      const winners: BonusWinner[] = [];
      scores.forEach(score => {
        if (score.bonuses && score.bonuses.length > 0) {
          score.bonuses.forEach(bonus => {
            winners.push({
              ...bonus,
              team_id: score.team_id,
              team_name: score.team_name
            });
          });
        }
      });

      setBonusWinners(winners);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bonus winners');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  if (bonusWinners.length === 0) {
    return (
      <div className="card p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <TrophyIcon className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Bonus Winners Yet</h3>
        <p className="text-gray-600">Weekly bonuses will appear here once games are played and stats are calculated.</p>
      </div>
    );
  }

  // Group bonuses by category for better display
  const bonusesByCategory = bonusWinners.reduce((acc, winner) => {
    if (!acc[winner.category]) {
      acc[winner.category] = [];
    }
    acc[winner.category].push(winner);
    return acc;
  }, {} as Record<string, BonusWinner[]>);

  return (
    <div className="card">
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrophyIcon className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          </div>
          {showWeekSelector && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <CalendarIcon className="w-4 h-4" />
              <span>Week {currentWeek}</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-6">
        <div className="grid gap-6">
          {Object.entries(bonusesByCategory).map(([category, winners]) => {
            const categoryInfo = BONUS_CATEGORIES[category as keyof typeof BONUS_CATEGORIES] || {
              label: category,
              icon: '🏆',
              color: 'bg-gray-100 text-gray-800 border-gray-200',
              description: 'Weekly performance bonus'
            };

            return (
              <div key={category} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-4">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 ${categoryInfo.color}`}>
                    <span className="text-xl">{categoryInfo.icon}</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{categoryInfo.label}</h3>
                    <p className="text-sm text-gray-600">{categoryInfo.description}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  {winners.map((winner, index) => (
                    <div key={index} className="flex items-center justify-between bg-white rounded-lg p-3 shadow-sm">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-blue-600">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{winner.player_name}</p>
                          <p className="text-sm text-gray-600">{winner.team_name}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-lg font-bold text-green-600">+{winner.points}</span>
                        <p className="text-xs text-gray-500">bonus pts</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WeeklyBonusWinners;