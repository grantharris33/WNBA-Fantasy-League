import React from 'react';
import type { BonusDetail } from '../../types';

interface PlayerBonusBadgeProps {
  playerName: string;
  bonuses: BonusDetail[];
  variant?: 'small' | 'normal';
}

const BONUS_CATEGORIES = {
  'top_scorer': {
    label: 'Top Scorer',
    icon: '🏀',
    color: 'bg-orange-100 text-orange-800 border-orange-200'
  },
  'top_rebounder': {
    label: 'Top Rebounder',
    icon: '💪',
    color: 'bg-blue-100 text-blue-800 border-blue-200'
  },
  'top_playmaker': {
    label: 'Top Playmaker',
    icon: '🎯',
    color: 'bg-green-100 text-green-800 border-green-200'
  },
  'defensive_beast': {
    label: 'Defensive Beast',
    icon: '🛡️',
    color: 'bg-purple-100 text-purple-800 border-purple-200'
  },
  'efficiency_award': {
    label: 'Efficiency Award',
    icon: '📊',
    color: 'bg-cyan-100 text-cyan-800 border-cyan-200'
  },
  'double_double_streak': {
    label: 'Double-Double Streak',
    icon: '⚡',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200'
  },
  'triple_double': {
    label: 'Triple-Double',
    icon: '👑',
    color: 'bg-red-100 text-red-800 border-red-200'
  }
};

const PlayerBonusBadge: React.FC<PlayerBonusBadgeProps> = ({
  playerName,
  bonuses,
  variant = 'normal'
}) => {
  // Filter bonuses that belong to this player
  const playerBonuses = bonuses.filter(bonus => bonus.player_name === playerName);

  if (playerBonuses.length === 0) {
    return null;
  }

  const totalBonusPoints = playerBonuses.reduce((sum, bonus) => sum + bonus.points, 0);

  if (variant === 'small') {
    return (
      <div className="flex flex-wrap gap-1">
        {playerBonuses.map((bonus, idx) => {
          const categoryInfo = BONUS_CATEGORIES[bonus.category as keyof typeof BONUS_CATEGORIES] || {
            label: bonus.category,
            icon: '🏆',
            color: 'bg-gray-100 text-gray-800 border-gray-200'
          };

          return (
            <span
              key={idx}
              className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium border ${categoryInfo.color}`}
              title={`${categoryInfo.label}: +${bonus.points} pts`}
            >
              <span className="text-xs">{categoryInfo.icon}</span>
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center space-x-1">
        <span className="text-xs font-medium text-green-600">
          +{totalBonusPoints} bonus pts
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {playerBonuses.map((bonus, idx) => {
          const categoryInfo = BONUS_CATEGORIES[bonus.category as keyof typeof BONUS_CATEGORIES] || {
            label: bonus.category,
            icon: '🏆',
            color: 'bg-gray-100 text-gray-800 border-gray-200'
          };

          return (
            <span
              key={idx}
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${categoryInfo.color}`}
              title={`${categoryInfo.label}: +${bonus.points} pts`}
            >
              <span className="mr-1">{categoryInfo.icon}</span>
              +{bonus.points}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default PlayerBonusBadge;