import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { user, logout } = useAuth();

  const sidebarLinks = [
    { to: '/', label: 'Dashboard', icon: 'dashboard' },
    { to: '/scoreboard', label: 'League Standings', icon: 'emoji_events' },
    { to: '/my-teams', label: 'Team Stats', icon: 'bar_chart' },
    { to: '/games', label: 'Recent Activity', icon: 'history' },
    { to: '/players', label: 'Player Stats', icon: 'person' },
  ];

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="relative flex size-full min-h-screen flex-col bg-slate-50 group/design-root overflow-x-hidden text-[#0d141c]" style={{fontFamily: 'Manrope, "Noto Sans", sans-serif'}}>
      <div className="layout-container flex h-full grow flex-col">
        {/* Integrated Header */}
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 px-10 py-4 bg-white shadow-sm">
          <div className="flex items-center gap-3 text-primary-600">
            <span className="material-icons text-3xl text-[#0c7ff2]">sports_basketball</span>
            <h2 className="text-xl font-bold leading-tight tracking-[-0.015em] text-[#0d141c]">WNBA Fantasy League</h2>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <>
                <button className="flex max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 w-10 bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors">
                  <span className="material-icons text-2xl">notifications</span>
                </button>
                <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-slate-200 hover:border-[#0c7ff2] transition-all" style={{backgroundImage: 'url("https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face")'}}></div>
                <button
                  onClick={logout}
                  className="text-slate-600 hover:text-slate-800 text-sm font-medium transition-colors"
                >
                  Sign Out
                </button>
              </>
            )}
          </div>
        </header>

        <div className="flex flex-1">
          <aside className="w-72 bg-white border-r border-slate-200 p-6 shadow-sm">
            <nav className="flex flex-col gap-2">
              {sidebarLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActivePath(link.to)
                      ? 'bg-[#0c7ff2] text-white font-semibold shadow-md hover:bg-opacity-90'
                      : 'hover:bg-slate-100 text-slate-700 hover:text-[#0c7ff2]'
                  }`}
                >
                  <span className="material-icons">{link.icon}</span>
                  <p className="text-sm leading-normal">{link.label}</p>
                </Link>
              ))}
              <Link
                to="/help"
                className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-100 text-slate-700 hover:text-[#0c7ff2] transition-all mt-auto border-t border-slate-200 pt-4"
              >
                <span className="material-icons">help_outline</span>
                <p className="text-sm font-medium leading-normal">Help</p>
              </Link>
            </nav>
          </aside>
          <main className="flex-1 p-8 bg-slate-100 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;