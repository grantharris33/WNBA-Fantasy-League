import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, error, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    try {
      await login(username, password);
      navigate('/'); // Redirect to dashboard on success
    } catch {
      // Error is handled in AuthContext
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-sky-100 text-slate-900" style={{fontFamily: 'Manrope, sans-serif'}}>
      <div className="relative flex min-h-screen flex-col group/design-root overflow-x-hidden">
        <div className="layout-container flex h-full grow flex-col">
          {/* Header */}
          <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md shadow-sm">
            <div className="container mx-auto flex items-center justify-between whitespace-nowrap px-6 py-4">
              <div className="flex items-center gap-3 text-slate-800">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                  <path clipRule="evenodd" d="M12.0799 24L4 19.2479L9.95537 8.75216L18.04 13.4961L18.0446 4H29.9554L29.96 13.4961L38.0446 8.75216L44 19.2479L35.92 24L44 28.7521L38.0446 39.2479L29.96 34.5039L29.9554 44H18.0446L18.04 34.5039L9.95537 39.2479L4 28.7521L12.0799 24Z" fill="currentColor" fillRule="evenodd"></path>
                </svg>
                <h1 className="text-2xl font-bold tracking-tight">Fantasy Hoops</h1>
              </div>
              <nav className="hidden md:flex items-center gap-6">
                <Link className="text-slate-700 hover:text-blue-600 text-sm font-medium transition-colors" to="#">Home</Link>
                <Link className="text-slate-700 hover:text-blue-600 text-sm font-medium transition-colors" to="#">My League</Link>
                <Link className="text-slate-700 hover:text-blue-600 text-sm font-medium transition-colors" to="#">Players</Link>
                <Link className="text-slate-700 hover:text-blue-600 text-sm font-medium transition-colors" to="#">Standings</Link>
              </nav>
              <div className="hidden md:flex items-center">
                <button className="flex min-w-[90px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-blue-600 text-white text-sm font-semibold leading-normal tracking-wide shadow-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                  <span className="truncate">Sign Up</span>
                </button>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex flex-1 items-center justify-center py-12 sm:py-16 md:py-20">
            <div className="w-full max-w-md px-4 sm:px-6">
              <div className="bg-white p-8 shadow-xl rounded-2xl">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">Welcome Back!</h2>
                  <p className="mt-2 text-sm text-slate-600">Log in to manage your WNBA fantasy league.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1" htmlFor="username">Username</label>
                    <input 
                      autoComplete="username" 
                      className="form-input block w-full rounded-lg border-slate-300 bg-slate-50 py-3 px-4 text-slate-900 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-colors" 
                      id="username" 
                      name="username" 
                      placeholder="your_username" 
                      required 
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between">
                      <label className="block text-sm font-medium text-slate-700 mb-1" htmlFor="password">Password</label>
                      <Link className="text-sm font-medium text-blue-600 hover:text-blue-500" to="#">Forgot password?</Link>
                    </div>
                    <input 
                      autoComplete="current-password" 
                      className="form-input block w-full rounded-lg border-slate-300 bg-slate-50 py-3 px-4 text-slate-900 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-colors" 
                      id="password" 
                      name="password" 
                      placeholder="••••••••" 
                      required 
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>
                  <div>
                    <button 
                      className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-transform transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none" 
                      type="submit"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Logging in...' : 'Log In'}
                    </button>
                  </div>
                </form>
                <p className="mt-8 text-center text-sm text-slate-600">
                  Don't have an account?
                  <Link className="font-medium text-blue-600 hover:text-blue-500" to="#"> Sign up here</Link>
                </p>
              </div>
            </div>
          </main>

          {/* Footer */}
          <footer className="bg-slate-100 border-t border-slate-200 py-8 text-center">
            <p className="text-sm text-slate-500">© 2024 Fantasy Hoops. All rights reserved.</p>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;