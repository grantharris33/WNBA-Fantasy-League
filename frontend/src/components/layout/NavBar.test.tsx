import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AuthContext, { type AuthContextType } from '../../contexts/AuthContext';
import type { UserOut } from '../../types';
import NavBar from './NavBar';

// Mock react-router-dom's useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate,
}));

describe('NavBar Component', () => {
  const mockLogout = jest.fn();
  const mockLogin = jest.fn();

  const renderWithAuth = (authContextValue: Partial<AuthContextType>) => {
    const defaultAuthContext: AuthContextType = {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: mockLogin,
      logout: mockLogout,
    };

    return render(
      <AuthContext.Provider value={{ ...defaultAuthContext, ...authContextValue }}>
        <BrowserRouter>
          <NavBar />
        </BrowserRouter>
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    mockLogout.mockClear();
    mockLogin.mockClear();
    mockedNavigate.mockClear();
  });

  test('renders WNBA Fantasy League title', () => {
    renderWithAuth({});
    expect(screen.getByText('WNBA Fantasy League')).toBeInTheDocument();
  });

  const testUser: UserOut = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    is_active: true,
    is_superuser: false,
    created_at: '2023-01-01T00:00:00Z'
  };

  test('displays user email and logout button when authenticated', () => {
    renderWithAuth({ user: testUser, isAuthenticated: true });
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  test('does not display user email when not authenticated', () => {
    renderWithAuth({ user: null, isAuthenticated: false });
    expect(screen.queryByText('test@example.com')).not.toBeInTheDocument();
  });

  test('calls logout function on logout button click', () => {
    renderWithAuth({ user: testUser, isAuthenticated: true });
    fireEvent.click(screen.getByRole('button', { name: /logout/i }));
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('title links to homepage', () => {
    renderWithAuth({});
    const titleLink = screen.getByText('WNBA Fantasy League').closest('a');
    expect(titleLink).toHaveAttribute('href', '/');
  });
});