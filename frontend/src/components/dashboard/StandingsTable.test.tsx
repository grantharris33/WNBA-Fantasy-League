import { render, screen } from '@testing-library/react';
import StandingsTable from './StandingsTable';
import type { TeamScoreData } from '../../types';

describe('StandingsTable Component', () => {
  const mockScores: TeamScoreData[] = [
    {
      team_id: 1,
      team_name: 'Winners',
      owner_name: 'Alice',
      season_points: 150,
      weekly_change: 10,
      weekly_bonuses: [{ reason: 'Top Scorer', points: 5 }],
    },
    {
      team_id: 2,
      team_name: 'Challengers',
      owner_name: 'Bob',
      season_points: 160,
      weekly_change: -5,
      weekly_bonuses: [],
    },
    {
      team_id: 3,
      team_name: 'Underdogs',
      owner_name: 'Charlie',
      season_points: 120,
      weekly_change: 20,
      weekly_bonuses: [
        { reason: 'Comeback King', points: 10 },
        { reason: 'Streak Bonus', points: 3 },
      ],
    },
  ];

  test('renders table headers correctly', () => {
    render(<StandingsTable scores={mockScores} />);
    expect(screen.getByRole('columnheader', { name: /rank/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /team name/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /owner/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /season points/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /weekly Δ/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /weekly bonuses/i })).toBeInTheDocument();
  });

  test('renders scores sorted by season points (descending) with correct rank', () => {
    render(<StandingsTable scores={mockScores} />);
    const rows = screen.getAllByRole('row'); // Includes header row

    // Check Challengers (160 pts) - Rank 1
    expect(rows[1]).toHaveTextContent('1'); // Rank
    expect(rows[1]).toHaveTextContent('Challengers');
    expect(rows[1]).toHaveTextContent('160');

    // Check Winners (150 pts) - Rank 2
    expect(rows[2]).toHaveTextContent('2'); // Rank
    expect(rows[2]).toHaveTextContent('Winners');
    expect(rows[2]).toHaveTextContent('150');

    // Check Underdogs (120 pts) - Rank 3
    expect(rows[3]).toHaveTextContent('3'); // Rank
    expect(rows[3]).toHaveTextContent('Underdogs');
    expect(rows[3]).toHaveTextContent('120');
  });

  test('displays team data correctly in rows', () => {
    render(<StandingsTable scores={mockScores} />);
    // Check for Alice's team (Winners)
    expect(screen.getByRole('cell', { name: 'Winners' })).toBeInTheDocument();
    expect(screen.getByRole('cell', { name: 'Alice' })).toBeInTheDocument();
    expect(screen.getByText('+10')).toBeInTheDocument(); // Weekly change for Winners
    expect(screen.getByText(/Top Scorer: \+5 pts/i)).toBeInTheDocument();
  });

  test('displays multiple bonuses correctly', () => {
    render(<StandingsTable scores={mockScores} />);
    expect(screen.getByText(/Comeback King: \+10 pts/i)).toBeInTheDocument();
    expect(screen.getByText(/Streak Bonus: \+3 pts/i)).toBeInTheDocument();
  });

  test('handles empty scores array', () => {
    render(<StandingsTable scores={[]} />);
    expect(screen.getByText(/no standings data available currently/i)).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  test('displays N/A for missing owner name', () => {
    const scoresWithMissingOwner: TeamScoreData[] = [
      { team_id: 4, team_name: 'Solo Act', season_points: 100, weekly_change: 5, weekly_bonuses: [], owner_name: undefined },
    ];
    render(<StandingsTable scores={scoresWithMissingOwner} />);
    expect(screen.getByRole('cell', { name: 'N/A' })).toBeInTheDocument();
  });

   test('formats weekly change colors correctly', () => {
    render(<StandingsTable scores={mockScores} />);
    const positiveChange = screen.getByText('+10');
    const negativeChange = screen.getByText('-5');
    expect(positiveChange).toHaveClass('text-green-600');
    expect(negativeChange).toHaveClass('text-red-600');
  });
});