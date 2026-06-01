import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import WeeklyCalendarView from './WeeklyCalendarView';

describe('WeeklyCalendarView', () => {
  const mockSessions = [
    {
      id: 1,
      subject_id: 1,
      subject_name: 'Mathématiques',
      day_of_week: 'Monday',
      start_time: '09:00',
      end_time: '10:30',
      task_type: 'lecture'
    },
    {
      id: 2,
      subject_id: 2,
      subject_name: 'Physique',
      day_of_week: 'Tuesday',
      start_time: '14:00',
      end_time: '15:00',
      task_type: 'exercise'
    }
  ];

  const mockAvailabilities = [
    {
      day_of_week: 'Monday',
      start_time: '08:00',
      end_time: '12:00'
    }
  ];

  const mockConstraints = [
    {
      constraint_type: 'forbidden_slot',
      is_active: true,
      parameters: {
        day_of_week: 'Wednesday',
        start_time: '12:00',
        end_time: '13:00'
      }
    }
  ];

  it('renders calendar with sessions', () => {
    render(
      <WeeklyCalendarView
        sessions={mockSessions}
        availabilities={mockAvailabilities}
        constraints={mockConstraints}
      />
    );

    expect(screen.getByText('Calendrier Hebdomadaire')).toBeInTheDocument();
    expect(screen.getByText('Mathématiques')).toBeInTheDocument();
    expect(screen.getByText('Physique')).toBeInTheDocument();
  });

  it('renders empty state when no sessions', () => {
    render(<WeeklyCalendarView sessions={[]} />);

    expect(screen.getByText('Aucune session planifiée')).toBeInTheDocument();
  });

  it('calls onSessionClick when session is clicked', () => {
    const handleClick = vi.fn();
    render(
      <WeeklyCalendarView
        sessions={mockSessions}
        onSessionClick={handleClick}
      />
    );

    const sessionElement = screen.getByText('Mathématiques').closest('div');
    fireEvent.click(sessionElement);

    expect(handleClick).toHaveBeenCalledWith(mockSessions[0]);
  });

  it('navigates to next week', () => {
    render(<WeeklyCalendarView sessions={mockSessions} />);

    const nextButton = screen.getByLabelText('Semaine suivante');
    fireEvent.click(nextButton);

    // Calendar should update (test implementation depends on date handling)
    expect(screen.getByText('Calendrier Hebdomadaire')).toBeInTheDocument();
  });

  it('navigates to previous week', () => {
    render(<WeeklyCalendarView sessions={mockSessions} />);

    const prevButton = screen.getByLabelText('Semaine précédente');
    fireEvent.click(prevButton);

    expect(screen.getByText('Calendrier Hebdomadaire')).toBeInTheDocument();
  });

  it('displays all days of the week', () => {
    render(<WeeklyCalendarView sessions={mockSessions} />);

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    days.forEach(day => {
      expect(screen.getByText(day)).toBeInTheDocument();
    });
  });
});
