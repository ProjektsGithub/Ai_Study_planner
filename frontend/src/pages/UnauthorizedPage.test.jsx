import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { LanguageProvider } from '../context/LanguageContext';
import UnauthorizedPage from './UnauthorizedPage';

// Mock useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
  };
});

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

describe('UnauthorizedPage', () => {
  it('renders 403 title and text', () => {
    render(
      <LanguageProvider>
        <MemoryRouter>
          <UnauthorizedPage />
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('403')).toBeInTheDocument();
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText('You do not have the required permissions to access this page.')).toBeInTheDocument();
    expect(screen.getByText('Back to Home')).toBeInTheDocument();
  });

  it('navigates to home when button is clicked', () => {
    const mockNavigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);

    render(
      <LanguageProvider>
        <MemoryRouter>
          <UnauthorizedPage />
        </MemoryRouter>
      </LanguageProvider>
    );

    const button = screen.getByText('Back to Home');
    fireEvent.click(button);
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
