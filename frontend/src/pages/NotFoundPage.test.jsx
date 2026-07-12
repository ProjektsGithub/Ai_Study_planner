import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { LanguageProvider } from '../context/LanguageContext';
import NotFoundPage from './NotFoundPage';

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

describe('NotFoundPage', () => {
  it('renders 404 title and text', () => {
    render(
      <LanguageProvider>
        <MemoryRouter>
          <NotFoundPage />
        </MemoryRouter>
      </LanguageProvider>
    );

    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Seite nicht gefunden')).toBeInTheDocument();
    expect(screen.getByText('Die gesuchte Seite existiert nicht oder wurde verschoben.')).toBeInTheDocument();
    expect(screen.getByText('Zurück zur Startseite')).toBeInTheDocument();
  });

  it('navigates to home when button is clicked', () => {
    const mockNavigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);

    render(
      <LanguageProvider>
        <MemoryRouter>
          <NotFoundPage />
        </MemoryRouter>
      </LanguageProvider>
    );

    const button = screen.getByText('Zurück zur Startseite');
    fireEvent.click(button);
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
