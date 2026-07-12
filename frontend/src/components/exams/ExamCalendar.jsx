import { useState } from 'react';
import PropTypes from 'prop-types';

const ExamCalendar = ({ exams = [], onExamClick }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // First day of month
  const firstDay = new Date(year, month, 1).getDay();
  // Adjust so Monday is 0 (firstDay is 0 for Sunday, 1 for Monday...)
  const firstDayAdjusted = firstDay === 0 ? 6 : firstDay - 1;

  // Total days in month
  const totalDays = new Date(year, month + 1, 0).getDate();

  // Month names
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const getExamsForDay = (day) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return exams.filter((e) => e.exam_date === dateStr);
  };

  const calendarDays = [];
  // Fill empty days before month start
  for (let i = 0; i < firstDayAdjusted; i++) {
    calendarDays.push(null);
  }
  // Fill actual month days
  for (let i = 1; i <= totalDays; i++) {
    calendarDays.push(i);
  }

  return (
    <div className="space-y-4">
      {/* Calendar Header Controls */}
      <div className="flex justify-between items-center bg-white/[0.02] border border-white/5 p-4 rounded-xl">
        <h2 className="text-base font-bold text-white">
          {monthNames[month]} {year}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handlePrevMonth}
            className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/5 transition-all border border-white/5"
            aria-label="Previous month"
          >
            &lt;
          </button>
          <button
            onClick={handleNextMonth}
            className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/5 transition-all border border-white/5"
            aria-label="Next month"
          >
            &gt;
          </button>
        </div>
      </div>

      {/* Grid structure */}
      <div className="border border-white/10 bg-white/[0.02] backdrop-blur-md rounded-2xl overflow-hidden shadow-card">
        {/* Days of week header */}
        <div className="grid grid-cols-7 border-b border-white/10 bg-white/[0.02] text-center text-xs font-semibold text-white/40 py-2.5">
          <span>Mon</span>
          <span>Tue</span>
          <span>Wed</span>
          <span>Thu</span>
          <span>Fri</span>
          <span>Sat</span>
          <span>Sun</span>
        </div>

        {/* Calendar days grid */}
        <div className="grid grid-cols-7 auto-rows-[100px] divide-x divide-y divide-white/5 border-l border-t border-white/5">
          {calendarDays.map((day, idx) => {
            const dayExams = day ? getExamsForDay(day) : [];
            return (
              <div key={idx} className="p-2 flex flex-col justify-between min-w-0 overflow-hidden relative group hover:bg-white/[0.01] transition-colors">
                <span className={`text-xs font-semibold ${day ? 'text-white/60' : 'text-transparent'}`}>
                  {day}
                </span>

                {dayExams.length > 0 && (
                  <div className="space-y-1 overflow-y-auto max-h-[70px] mt-1 pr-0.5">
                    {dayExams.map((exam) => (
                      <button
                        key={exam.id}
                        type="button"
                        onClick={() => onExamClick(exam)}
                        className="w-full text-left truncate text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 border border-blue-500/30 text-blue-300 hover:bg-blue-500/35 transition-colors font-medium"
                        title={exam.course_name}
                      >
                        {exam.course_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

ExamCalendar.propTypes = {
  exams: PropTypes.array,
  onExamClick: PropTypes.func.isRequired,
};

export default ExamCalendar;
