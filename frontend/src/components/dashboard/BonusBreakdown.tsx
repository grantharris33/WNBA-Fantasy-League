import React from 'react';
import { TrophyIcon, StarIcon } from '@heroicons/react/24/outline';
import type { BonusDetail } from '../../types';

interface BonusBreakdownProps {
  bonuses: BonusDetail[];
  teamName?: string;
  showTitle?: boolean;
  variant?: 'card' | 'inline' | 'detailed';
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

const BonusBreakdown: React.FC<BonusBreakdownProps> = ({
  bonuses,
  teamName,
  showTitle = true,
  variant = 'card'
}) => {
  if (!bonuses || bonuses.length === 0) {
    if (variant === 'inline') {
      return <span className="text-gray-400 text-sm">No bonuses this week</span>;
    }

    return (
      <div className={`${variant === 'card' ? 'card p-6' : 'p-4'} text-center`}>
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <TrophyIcon className="w-8 h-8 text-gray-400" />
        </div>
        <p className="text-gray-500 text-sm">No weekly bonuses earned yet</p>
      </div>
    );
  }

  const totalBonusPoints = bonuses.reduce((sum, bonus) => sum + bonus.points, 0);

  if (variant === 'inline') {
    return (
      <div className="flex flex-wrap gap-1">
        {bonuses.map((bonus, idx) => {
          const categoryInfo = BONUS_CATEGORIES[bonus.category as keyof typeof BONUS_CATEGORIES] || {
            label: bonus.category,
            icon: '🏆',
            color: 'bg-gray-100 text-gray-800 border-gray-200'
          };

          return (
            <span
              key={idx}
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${categoryInfo.color}`}
              title={`${categoryInfo.label}: +${bonus.points} pts (${bonus.player_name})`}
            >
              <span className="mr-1">{categoryInfo.icon}</span>
              +{bonus.points}
            </span>
          );
        })}
      </div>
    );
  }

  const BonusItem: React.FC<{ bonus: BonusDetail; index: number }> = ({ bonus }) => {
    const categoryInfo = BONUS_CATEGORIES[bonus.category as keyof typeof BONUS_CATEGORIES] || {
      label: bonus.category,
      icon: '🏆',
      color: 'bg-gray-100 text-gray-800 border-gray-200',
      description: 'Weekly performance bonus'
    };

    return (
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border ${categoryInfo.color}`}>
            <span className="text-lg">{categoryInfo.icon}</span>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-900">{categoryInfo.label}</h4>
            <p className="text-xs text-gray-600">{bonus.player_name}</p>
            {variant === 'detailed' && (
              <p className="text-xs text-gray-500 mt-1">{categoryInfo.description}</p>
            )}
          </div>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-green-600">+{bonus.points}</span>
          <p className="text-xs text-gray-500">pts</p>
        </div>
      </div>
    );
  };

  return (
    <div className={variant === 'card' ? 'card' : ''}>
      {showTitle && (
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <StarIcon className="w-5 h-5 text-yellow-500" />
            <h3 className="text-lg font-semibold text-gray-900">
              {teamName ? `${teamName} Weekly Bonuses` : 'Weekly Bonuses'}
            </h3>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold text-green-600">+{totalBonusPoints}</span>
            <p className="text-sm text-gray-500">total bonus pts</p>
          </div>
        </div>
      )}

      <div className={`${variant === 'card' ? 'p-4' : ''} space-y-3`}>
        {bonuses.map((bonus, index) => (
          <BonusItem key={index} bonus={bonus} index={index} />
        ))}
      </div>
    </div>
  );
};

export default BonusBreakdown;