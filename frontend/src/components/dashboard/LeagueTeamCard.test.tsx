import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LeagueTeamCard from './LeagueTeamCard';
import type { UserTeam } from '../../types';
import type { DraftState as DraftStateType } from '../../types';

// Define the structure for draft status info passed as a prop, mirroring LeagueTeamCard
interface DraftStatusInfoProp {
  leagueId: number;
  status: DraftStateType['status'] | 'loading' | 'error';
  error?: string;
}

describe('LeagueTeamCard Component', () => {
  const mockTeam: UserTeam = {
    id: 101,
    name: 'My Awesome Team',
    league_id: 1,
    league: { id: 1, name: 'Global Super League' },
  };

  const renderCard = (team: UserTeam, draftStatusInfo?: DraftStatusInfoProp) => {
    return render(
      <BrowserRouter>
        <LeagueTeamCard team={team} draftStatusInfo={draftStatusInfo} />
      </BrowserRouter>
    );
  };

  test('renders league name and team name', () => {
    renderCard(mockTeam);
    expect(screen.getByText('Global Super League')).toBeInTheDocument();
    expect(screen.getByText(/Your Team: My Awesome Team/i)).toBeInTheDocument();
  });

  test('renders View Draft and Manage Team links', () => {
    renderCard(mockTeam);
    const draftLink = screen.getByRole('link', { name: /view draft/i });
    const manageLink = screen.getByRole('link', { name: /manage team/i });

    expect(draftLink).toBeInTheDocument();
    expect(draftLink).toHaveAttribute('href', '/draft/1');
    expect(manageLink).toBeInTheDocument();
    expect(manageLink).toHaveAttribute('href', '/team/101');
  });

  test('shows loading state for draft status', () => {
    renderCard(mockTeam, { leagueId: 1, status: 'loading' });
    expect(screen.getByText('Loading draft status...')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /checking draft.../i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /checking draft.../i })).toHaveClass('cursor-not-allowed');
  });

  test('shows error state for draft status', () => {
    renderCard(mockTeam, { leagueId: 1, status: 'error', error: 'Network Error' });
    expect(screen.getByText(/Error: Network Error/i)).toBeInTheDocument();
    // Default button text might be "View Draft" or specific error indication
  });

  test('renders correctly for "pending" draft status', () => {
    renderCard(mockTeam, { leagueId: 1, status: 'pending' });
    expect(screen.getByText('Draft: Pending')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /draft not started/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /draft not started/i })).toHaveClass('cursor-not-allowed');
  });

  test('renders correctly for "active" draft status', () => {
    renderCard(mockTeam, { leagueId: 1, status: 'active' });
    expect(screen.getByText('Draft: Active')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /enter draft room/i })).toBeInTheDocument();
  });

  test('renders correctly for "completed" draft status', () => {
    renderCard(mockTeam, { leagueId: 1, status: 'completed' });
    expect(screen.getByText('Draft: Completed')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view draft results/i })).toBeInTheDocument();
  });

  test('handles missing league name gracefully', () => {
    const teamWithoutLeagueName = { ...mockTeam, league: undefined };
    renderCard(teamWithoutLeagueName);
    expect(screen.getByText(`League ID: ${mockTeam.league_id}`)).toBeInTheDocument();
  });
});