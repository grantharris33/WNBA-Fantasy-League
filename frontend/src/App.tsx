import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DraftPage from './pages/DraftPage';
import TeamPage from './pages/TeamPage';
import JoinLeaguePage from './pages/JoinLeaguePage';
import LeagueManagementPage from './pages/LeagueManagementPage';
import LeagueDetailPage from './pages/LeagueDetailPage';
import MyTeamsPage from './pages/MyTeamsPage';
import ScoreboardPage from './pages/ScoreboardPage';
import GameDetailPage from './pages/GameDetailPage';
import GamesPage from './pages/GamesPage';
import PlayersPage from './pages/PlayersPage';
import PlayerDetailPage from './pages/PlayerDetailPage';
import BonusesPage from './pages/BonusesPage';
import HelpPage from './pages/HelpPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';
import SignupPage from './pages/SignupPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/scoreboard" element={<ScoreboardPage />} />
            <Route path="/join" element={<JoinLeaguePage />} />
            <Route path="/my-teams" element={<MyTeamsPage />} />
            <Route path="/league/:leagueId" element={<LeagueDetailPage />} />
            <Route path="/league/:leagueId/manage" element={<LeagueManagementPage />} />
            <Route path="/draft/:leagueId" element={<DraftPage />} />
            <Route path="/team/:teamId" element={<TeamPage />} />
            <Route path="/games" element={<GamesPage />} />
            <Route path="/game/:gameId" element={<GameDetailPage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/player/:playerId" element={<PlayerDetailPage />} />
            <Route path="/bonuses" element={<BonusesPage />} />
            <Route path="/help" element={<HelpPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>

          {/* Redirect to home for undefined routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <ToastContainer
          position="bottom-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="colored"
        />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
