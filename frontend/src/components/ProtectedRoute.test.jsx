import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LanguageProvider } from '../context/LanguageContext';
import ProtectedRoute from './ProtectedRoute';

// Mock useAuth
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

describe('ProtectedRoute', () => {
  it('renders loading spinner when loading is true', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      loading: true,
      hasRole: vi.fn(),
    });

    render(
      <LanguageProvider>
        <MemoryRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      loading: false,
      hasRole: vi.fn(),
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route path="/protected" element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders UnauthorizedPage when user does not have allowed roles', () => {
    const hasRoleMock = vi.fn().mockReturnValue(false);
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      loading: false,
      hasRole: hasRoleMock,
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route path="/protected" element={
              <ProtectedRoute allowedRoles={['super_admin']}>
                <div>Protected Content</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user is authenticated and has correct role', () => {
    const hasRoleMock = vi.fn().mockImplementation((role) => role === 'super_admin');
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      loading: false,
      hasRole: hasRoleMock,
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route path="/protected" element={
              <ProtectedRoute allowedRoles={['super_admin']}>
                <div>Protected Content</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});
