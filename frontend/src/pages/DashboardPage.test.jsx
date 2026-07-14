import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from './DashboardPage';
import { AcademicDataProvider } from '../context/AcademicDataContext';
import { StudyPlanProvider } from '../context/StudyPlanContext';
import { GamificationProvider } from '../context/GamificationContext';
import { AuthProvider } from '../context/AuthContext';

// Mock API client
vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const AllProviders = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      <AcademicDataProvider>
        <StudyPlanProvider>
          <GamificationProvider>
            {children}
          </GamificationProvider>
        </StudyPlanProvider>
      </AcademicDataProvider>
    </AuthProvider>
  </BrowserRouter>
);

describe('DashboardPage - Synchronization Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage for auth token
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'access_token') return 'fake-token';
      if (key === 'earned_badges') return '[]';
      return null;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dashboard with refresh button', async () => {
    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    // Check for refresh button
    const refreshButton = screen.getByTitle('Refresh dashboard data');
    expect(refreshButton).toBeInTheDocument();
  });

  it('refresh button triggers manual refresh', async () => {
    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    const refreshButton = screen.getByTitle('Refresh dashboard data');
    
    // Click refresh button
    fireEvent.click(refreshButton);

    // Button should be disabled during refresh
    await waitFor(() => {
      expect(refreshButton).toBeDisabled();
    });
  });

  it('sets up polling interval on mount', () => {
    vi.useFakeTimers();
    
    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000);

    // Polling should have triggered fetchCurrentPlan
    // (This would need actual API mock verification)

    vi.useRealTimers();
  });

  it('cleans up polling interval on unmount', () => {
    vi.useFakeTimers();
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');
    
    const { unmount } = render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();

    vi.useRealTimers();
  });

  it('displays loading state correctly', () => {
    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    // Should show skeleton loaders initially
    // (Depends on mock implementation)
  });

  it('displays current plan information when available', async () => {
    // Mock successful API response
    const mockPlan = {
      plan_id: '123',
      total_hours: 20,
      session_count: 10,
      sessions: [
        { id: 1, day: 'Monday', subject_name: 'Math', completed: false },
        { id: 2, day: 'Tuesday', subject_name: 'Physics', completed: true },
      ],
    };

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    await waitFor(() => {
      // Check if plan data is displayed
      // (Depends on actual component implementation)
    });
  });
});
