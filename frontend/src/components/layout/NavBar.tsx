import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const NavBar: React.FC = () => {
  const { user } = useAuth();

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: 'home' },
    { to: '/my-teams', label: 'My Team', icon: 'sports_basketball' },
    { to: '/scoreboard', label: 'Scoreboard', icon: 'leaderboard' },
    { to: '/players', label: 'Player Stats', icon: 'bar_chart' },
    { to: '/draft', label: 'Draft Room', icon: 'groups' },
    { to: '/join', label: 'Join League', icon: 'add_circle' },
    ...(user?.is_admin ? [{ to: '/admin', label: 'Admin', icon: 'settings' }] : []),
  ];



  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 px-10 py-4 bg-white shadow-sm">
      <div className="flex items-center gap-3 text-primary-600">
        <span className="material-icons text-3xl text-[#0c7ff2]">sports_basketball</span>
        <h2 className="text-xl font-bold leading-tight tracking-[-0.015em] text-[#0d141c]">WNBA Fantasy League</h2>
      </div>

      {user && (
        <nav className="flex flex-1 justify-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="text-slate-700 hover:text-[#0c7ff2] text-sm font-medium leading-normal transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      )}

      <div className="flex items-center gap-4">
        {user && (
          <>
            <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 w-10 bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors">
              <span className="material-icons text-2xl">notifications</span>
            </button>
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-slate-200 hover:border-[#0c7ff2] transition-all" style={{backgroundImage: 'url("https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face")'}}></div>
          </>
        )}

        {!user && (
          <button
            onClick={() => window.location.href = '/login'}
            className="flex min-w-[90px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-[#0c7ff2] text-white text-sm font-semibold leading-normal tracking-wide shadow-md hover:bg-[#0a68c4] transition-colors"
          >
            <span className="truncate">Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default NavBar;