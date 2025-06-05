import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface TeamManagementLayoutProps {
  children: React.ReactNode;
  teamName?: string;
}

const TeamManagementLayout: React.FC<TeamManagementLayoutProps> = ({ children, teamName = "My Team" }) => {
  const location = useLocation();

  const sidebarLinks = [
    { to: '/my-teams', label: 'Team Overview', icon: 'bar_chart' },
    { to: '/team/lineup', label: 'Lineup', icon: 'groups' },
    { to: '/team/matchup', label: 'Matchup', icon: 'sports_basketball' },
    { to: '/team/stats', label: 'Stats', icon: 'query_stats' },
  ];

  const isActivePath = (path: string) => {
    return location.pathname.includes(path);
  };

  return (
    <div className="bg-slate-100" style={{fontFamily: 'Manrope, "Noto Sans", sans-serif'}}>
      <div className="relative flex size-full min-h-screen flex-col group/design-root overflow-x-hidden">
        <div className="layout-container flex h-full grow flex-col">
          {/* Header */}
          <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 bg-white px-6 py-4 shadow-sm">
            <div className="flex items-center gap-3 text-slate-900">
              <div className="size-8 text-[#0c7ff2]">
                <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                  <path clipRule="evenodd" d="M12.0799 24L4 19.2479L9.95537 8.75216L18.04 13.4961L18.0446 4H29.9554L29.96 13.4961L38.0446 8.75216L44 19.2479L35.92 24L44 28.7521L38.0446 39.2479L29.96 34.5039L29.9554 44H18.0446L18.04 34.5039L9.95537 39.2479L4 28.7521L12.0799 24Z" fill="currentColor" fillRule="evenodd"></path>
                </svg>
              </div>
              <h1 className="text-slate-900 text-xl font-bold tracking-tight">Fantasy Hoops</h1>
            </div>
            <nav className="flex items-center gap-6">
              <Link className="text-slate-700 hover:text-[#0c7ff2] text-sm font-medium transition-colors" to="/my-teams">My Teams</Link>
              <Link className="text-slate-700 hover:text-[#0c7ff2] text-sm font-medium transition-colors" to="/players">Players</Link>
              <Link className="text-slate-700 hover:text-[#0c7ff2] text-sm font-medium transition-colors" to="/scoreboard">Standings</Link>
              <Link className="text-slate-700 hover:text-[#0c7ff2] text-sm font-medium transition-colors" to="/trade">Trade</Link>
            </nav>
            <div className="flex items-center gap-4">
              <button className="flex items-center justify-center rounded-full h-10 w-10 hover:bg-slate-100 text-slate-600 transition-colors">
                <span className="material-icons text-2xl">notifications</span>
              </button>
              <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-slate-200 shadow-sm" style={{backgroundImage: 'url("https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face")'}}></div>
            </div>
          </header>

          <div className="flex flex-1 px-6 py-8 gap-6">
            {/* Sidebar */}
            <aside className="flex flex-col w-72 bg-white rounded-xl shadow-lg p-6">
              <div className="mb-6">
                <h2 className="text-slate-900 text-lg font-semibold">{teamName}</h2>
                <p className="text-slate-500 text-sm">Season 2024</p>
              </div>
              <nav className="flex flex-col gap-2">
                {sidebarLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                      isActivePath(link.label.toLowerCase()) 
                        ? 'bg-[#0c7ff2]/10 text-[#0c7ff2]' 
                        : 'text-slate-700 hover:bg-slate-100 hover:text-[#0c7ff2]'
                    }`}
                  >
                    <span className={`material-icons ${
                      isActivePath(link.label.toLowerCase()) 
                        ? 'text-[#0c7ff2]' 
                        : 'text-slate-500 group-hover:text-[#0c7ff2]'
                    } transition-colors`}>{link.icon}</span>
                    <span className={`text-sm ${
                      isActivePath(link.label.toLowerCase()) ? 'font-bold' : 'font-medium'
                    }`}>{link.label}</span>
                  </Link>
                ))}
                <Link
                  to="/settings"
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-700 hover:bg-slate-100 hover:text-[#0c7ff2] transition-colors group mt-4 border-t border-slate-200 pt-4"
                >
                  <span className="material-icons text-slate-500 group-hover:text-[#0c7ff2] transition-colors">settings</span>
                  <span className="text-sm font-medium">Settings</span>
                </Link>
              </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col gap-6">
              {children}
            </main>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamManagementLayout;