import { useState, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * WeeklyCalendarView Component
 * Displays study sessions in a weekly calendar grid with day columns and time slot rows
 */
const WeeklyCalendarView = ({ 
  sessions = [], 
  availabilities = [], 
  constraints = [],
  onSessionClick,
  weekStartDate 
}) => {
  const [currentWeekStart, setCurrentWeekStart] = useState(
    weekStartDate || getMonday(new Date())
  );

  // Days of the week
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  // Time slots (30-minute increments from 00:00 to 23:30)
  const timeSlots = useMemo(() => {
    const slots = [];
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        slots.push(`${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`);
      }
    }
    return slots;
  }, []);

  // Generate dates for the current week
  const weekDates = useMemo(() => {
    return daysOfWeek.map((_, index) => {
      const date = new Date(currentWeekStart);
      date.setDate(date.getDate() + index);
      return date;
    });
  }, [currentWeekStart]);

  // Subject colors mapping
  const subjectColors = useMemo(() => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500',
      'bg-yellow-500', 'bg-indigo-500', 'bg-red-500', 'bg-teal-500',
      'bg-orange-500', 'bg-cyan-500'
    ];
    const colorMap = {};
    sessions.forEach((session, index) => {
      if (!colorMap[session.subject_id]) {
        colorMap[session.subject_id] = colors[Object.keys(colorMap).length % colors.length];
      }
    });
    return colorMap;
  }, [sessions]);

  // Check if a time slot has availability
  const hasAvailability = (dayIndex, timeSlot) => {
    const dayName = daysOfWeek[dayIndex];
    return availabilities.some(avail => 
      avail.day_of_week === dayName &&
      timeSlot >= avail.start_time &&
      timeSlot < avail.end_time
    );
  };

  // Check if a time slot has constraints
  const hasConstraint = (dayIndex, timeSlot) => {
    const dayName = daysOfWeek[dayIndex];
    return constraints.some(constraint => {
      if (!constraint.is_active) return false;
      
      if (constraint.constraint_type === 'forbidden_slot') {
        const params = constraint.parameters;
        return params.day_of_week === dayName &&
               timeSlot >= params.start_time &&
               timeSlot < params.end_time;
      }
      return false;
    });
  };

  // Get sessions for a specific day and time slot
  const getSessionsForSlot = (dayIndex, timeSlot) => {
    const dayName = daysOfWeek[dayIndex];
    return sessions.filter(session => 
      session.day_of_week === dayName &&
      timeSlot >= session.start_time &&
      timeSlot < session.end_time
    );
  };

  // Calculate session span (how many 30-min slots it occupies)
  const calculateSessionSpan = (session) => {
    const [startHour, startMin] = session.start_time.split(':').map(Number);
    const [endHour, endMin] = session.end_time.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    return Math.ceil((endMinutes - startMinutes) / 30);
  };

  // Check if this is the first slot of a session
  const isFirstSlotOfSession = (session, timeSlot) => {
    return session.start_time === timeSlot;
  };

  // Navigation handlers
  const goToPreviousWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() - 7);
    setCurrentWeekStart(newDate);
  };

  const goToNextWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() + 7);
    setCurrentWeekStart(newDate);
  };

  const goToCurrentWeek = () => {
    setCurrentWeekStart(getMonday(new Date()));
  };

  // Format date for display
  const formatDate = (date) => {
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
  };

  // Empty state
  if (sessions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune session planifiée</h3>
          <p className="mt-1 text-sm text-gray-500">
            Générez un plan d'étude pour voir votre calendrier hebdomadaire.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header with navigation */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Calendrier Hebdomadaire
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Semaine du {formatDate(weekDates[0])} au {formatDate(weekDates[6])}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPreviousWeek}
              className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              aria-label="Semaine précédente"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={goToCurrentWeek}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
            >
              Aujourd'hui
            </button>
            <button
              onClick={goToNextWeek}
              className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              aria-label="Semaine suivante"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full align-middle">
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              {/* Header with days */}
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="w-20 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                    Heure
                  </th>
                  {daysOfWeek.map((day, index) => (
                    <th
                      key={day}
                      className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                    >
                      <div>{day}</div>
                      <div className="text-gray-400 font-normal mt-1">
                        {formatDate(weekDates[index])}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>

              {/* Time slots */}
              <tbody className="bg-white divide-y divide-gray-200">
                {timeSlots.map((timeSlot) => (
                  <tr key={timeSlot} className="h-12">
                    {/* Time column */}
                    <td className="px-3 py-2 text-xs text-gray-500 border-r border-gray-200 whitespace-nowrap">
                      {timeSlot}
                    </td>

                    {/* Day columns */}
                    {daysOfWeek.map((day, dayIndex) => {
                      const sessionsInSlot = getSessionsForSlot(dayIndex, timeSlot);
                      const hasAvail = hasAvailability(dayIndex, timeSlot);
                      const hasConstr = hasConstraint(dayIndex, timeSlot);

                      return (
                        <td
                          key={`${day}-${timeSlot}`}
                          className={`relative px-1 py-1 border-r border-gray-200 last:border-r-0 ${
                            hasAvail ? 'bg-green-50' : ''
                          } ${hasConstr ? 'bg-red-50' : ''}`}
                        >
                          {sessionsInSlot.map((session) => {
                            // Only render the session in its first slot
                            if (!isFirstSlotOfSession(session, timeSlot)) {
                              return null;
                            }

                            const span = calculateSessionSpan(session);
                            const color = subjectColors[session.subject_id];

                            return (
                              <div
                                key={session.id}
                                className={`absolute inset-x-1 ${color} text-white rounded px-2 py-1 text-xs cursor-pointer hover:opacity-90 transition-opacity overflow-hidden`}
                                style={{
                                  height: `calc(${span * 3}rem - 0.5rem)`,
                                  zIndex: 5
                                }}
                                onClick={() => onSessionClick && onSessionClick(session)}
                                title={`${session.subject_name} - ${session.task_type}\n${session.start_time} - ${session.end_time}`}
                              >
                                <div className="font-semibold truncate">
                                  {session.subject_name}
                                </div>
                                <div className="text-xs opacity-90 truncate">
                                  {session.task_type}
                                </div>
                                <div className="text-xs opacity-75">
                                  {session.start_time} - {session.end_time}
                                </div>
                              </div>
                            );
                          })}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
        <div className="flex items-center space-x-6 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-50 border border-green-200 rounded mr-2"></div>
            <span className="text-gray-600">Disponibilité</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-50 border border-red-200 rounded mr-2"></div>
            <span className="text-gray-600">Contrainte</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
            <span className="text-gray-600">Session d'étude</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get Monday of the current week
function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
  return new Date(d.setDate(diff));
}

WeeklyCalendarView.propTypes = {
  sessions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      subject_id: PropTypes.number.isRequired,
      subject_name: PropTypes.string.isRequired,
      day_of_week: PropTypes.string.isRequired,
      start_time: PropTypes.string.isRequired,
      end_time: PropTypes.string.isRequired,
      task_type: PropTypes.string.isRequired,
    })
  ),
  availabilities: PropTypes.arrayOf(
    PropTypes.shape({
      day_of_week: PropTypes.string.isRequired,
      start_time: PropTypes.string.isRequired,
      end_time: PropTypes.string.isRequired,
    })
  ),
  constraints: PropTypes.arrayOf(
    PropTypes.shape({
      constraint_type: PropTypes.string.isRequired,
      is_active: PropTypes.bool.isRequired,
      parameters: PropTypes.object.isRequired,
    })
  ),
  onSessionClick: PropTypes.func,
  weekStartDate: PropTypes.instanceOf(Date),
};

export default WeeklyCalendarView;
