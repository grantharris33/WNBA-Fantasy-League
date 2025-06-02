import { render, screen } from '@testing-library/react';
import StandingsTable from './StandingsTable';
import type { TeamScoreData } from '../../types';

const mockScores: TeamScoreData[] = [
  {
    team_id: 1,
    team_name: 'The Champs',
    season_points: 150,
    weekly_delta: 10,
    weekly_bonus_points: 5,
    bonuses: [
      { category: 'Top Scorer', points: 5, player_name: 'Jane Doe' }
    ],
    owner_name: 'Alice',
  },
  {
    team_id: 2,
    team_name: 'Underdogs',
    season_points: 120,
    weekly_delta: -5,
    weekly_bonus_points: 0,
    bonuses: [],
    owner_name: 'Bob',
  },
  {
    team_id: 3,
    team_name: 'Middle Ground',
    season_points: 135,
    weekly_delta: 20,
    weekly_bonus_points: 2,
    bonuses: [
      { category: 'Most Assists', points: 2, player_name: 'John Smith' }
    ],
    owner_name: 'Charlie',
  },
];

describe('StandingsTable', () => {
  it('renders team names and scores correctly', () => {
    render(<StandingsTable scores={mockScores} />);

    expect(screen.getByText('The Champs')).toBeInTheDocument();
    expect(screen.getByText('Underdogs')).toBeInTheDocument();
    expect(screen.getByText('Middle Ground')).toBeInTheDocument();

    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('135')).toBeInTheDocument();
  });

  it('shows correct ranking based on season points', () => {
    render(<StandingsTable scores={mockScores} />);

    const rows = screen.getAllByRole('row');
    // First row is header, so data starts from row[1]
    expect(rows[1]).toHaveTextContent('1'); // The Champs should be ranked 1st (150 points)
    expect(rows[2]).toHaveTextContent('2'); // Middle Ground should be ranked 2nd (135 points)
    expect(rows[3]).toHaveTextContent('3'); // Underdogs should be ranked 3rd (120 points)
  });

  it('displays weekly change with appropriate styling', () => {
    render(<StandingsTable scores={mockScores} />);

    // Check for positive change (green)
    const positiveChange = screen.getByText('+20');
    expect(positiveChange).toHaveClass('text-green-600');

    // Check for negative change (red)
    const negativeChange = screen.getByText('-5');
    expect(negativeChange).toHaveClass('text-red-600');
  });

  it('displays bonus details correctly', () => {
    render(<StandingsTable scores={mockScores} />);

    expect(screen.getByText(/Top Scorer.*5.*Jane Doe/)).toBeInTheDocument();
    expect(screen.getByText(/Most Assists.*2.*John Smith/)).toBeInTheDocument();
  });

  it('handles empty scores array', () => {
    render(<StandingsTable scores={[]} />);
    expect(screen.getByText('No standings data available currently.')).toBeInTheDocument();
  });

  it('sorts teams correctly by season points', () => {
    const unsortedScores: TeamScoreData[] = [
      { team_id: 4, team_name: 'Solo Act', season_points: 100, weekly_delta: 5, weekly_bonus_points: 0, bonuses: [], owner_name: undefined },
      { team_id: 5, team_name: 'Top Team', season_points: 200, weekly_delta: 15, weekly_bonus_points: 3, bonuses: [], owner_name: 'Dave' },
      { team_id: 6, team_name: 'Mid Team', season_points: 150, weekly_delta: 0, weekly_bonus_points: 1, bonuses: [], owner_name: 'Eve' },
    ];

    render(<StandingsTable scores={unsortedScores} />);

    const teamNames = screen.getAllByRole('cell').filter(cell =>
      cell.textContent === 'Top Team' || cell.textContent === 'Mid Team' || cell.textContent === 'Solo Act'
    );

    // Should be sorted: Top Team (200), Mid Team (150), Solo Act (100)
    expect(teamNames[0]).toHaveTextContent('Top Team');
    expect(teamNames[1]).toHaveTextContent('Mid Team');
    expect(teamNames[2]).toHaveTextContent('Solo Act');
  });
});