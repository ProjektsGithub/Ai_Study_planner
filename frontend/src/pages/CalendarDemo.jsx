import { useState } from 'react';
import WeeklyCalendarView from '../components/WeeklyCalendarView';
import SessionEditor from '../components/SessionEditor';

/**
 * CalendarDemo Component
 * Demonstration page with mock data for testing the calendar without backend
 */
const CalendarDemo = () => {
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  // Mock data
  const mockSessions = [
    {
      id: 1,
      subject_id: 1,
      subject_name: 'Mathématiques',
      day_of_week: 'Monday',
      start_time: '09:00',
      end_time: '10:30',
      task_type: 'lecture',
      notes: 'Chapitre 5: Intégrales'
    },
    {
      id: 2,
      subject_id: 2,
      subject_name: 'Physique',
      day_of_week: 'Monday',
      start_time: '14:00',
      end_time: '15:00',
      task_type: 'exercise',
      notes: 'Exercices sur la mécanique'
    },
    {
      id: 3,
      subject_id: 1,
      subject_name: 'Mathématiques',
      day_of_week: 'Tuesday',
      start_time: '10:00',
      end_time: '11:30',
      task_type: 'exercise',
      notes: 'TD intégrales'
    },
    {
      id: 4,
      subject_id: 3,
      subject_name: 'Informatique',
      day_of_week: 'Wednesday',
      start_time: '09:00',
      end_time: '12:00',
      task_type: 'project',
      notes: 'Projet web'
    },
    {
      id: 5,
      subject_id: 2,
      subject_name: 'Physique',
      day_of_week: 'Thursday',
      start_time: '14:00',
      end_time: '16:00',
      task_type: 'revision',
      notes: 'Révision pour examen'
    },
    {
      id: 6,
      subject_id: 4,
      subject_name: 'Anglais',
      day_of_week: 'Friday',
      start_time: '10:00',
      end_time: '11:00',
      task_type: 'reading',
      notes: 'Lecture chapitre 3'
    },
    {
      id: 7,
      subject_id: 3,
      subject_name: 'Informatique',
      day_of_week: 'Friday',
      start_time: '15:00',
      end_time: '17:00',
      task_type: 'practice',
      notes: 'Pratique algorithmes'
    }
  ];

  const mockAvailabilities = [
    { day_of_week: 'Monday', start_time: '08:00', end_time: '12:00' },
    { day_of_week: 'Monday', start_time: '14:00', end_time: '18:00' },
    { day_of_week: 'Tuesday', start_time: '09:00', end_time: '12:00' },
    { day_of_week: 'Tuesday', start_time: '14:00', end_time: '17:00' },
    { day_of_week: 'Wednesday', start_time: '08:00', end_time: '18:00' },
    { day_of_week: 'Thursday', start_time: '09:00', end_time: '18:00' },
    { day_of_week: 'Friday', start_time: '09:00', end_time: '17:00' }
  ];

  const mockConstraints = [
    {
      constraint_type: 'forbidden_slot',
      is_active: true,
      parameters: {
        day_of_week: 'Wednesday',
        start_time: '12:00',
        end_time: '14:00'
      }
    },
    {
      constraint_type: 'forbidden_slot',
      is_active: true,
      parameters: {
        day_of_week: 'Friday',
        start_time: '12:00',
        end_time: '13:00'
      }
    }
  ];

  const mockSubjects = [
    { id: 1, name: 'Mathématiques' },
    { id: 2, name: 'Physique' },
    { id: 3, name: 'Informatique' },
    { id: 4, name: 'Anglais' },
    { id: 5, name: 'Histoire' }
  ];

  const handleSessionClick = (session) => {
    setSelectedSession(session);
    setIsEditorOpen(true);
  };

  const handleSaveSession = async (sessionData) => {
    console.log('Save session:', sessionData);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    alert('Session sauvegardée (mode démo)');
  };

  const handleDeleteSession = async (sessionId) => {
    console.log('Delete session:', sessionId);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    alert('Session supprimée (mode démo)');
  };

  const handleCloseEditor = () => {
    setIsEditorOpen(false);
    setSelectedSession(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                📚 Calendrier Hebdomadaire - Mode Démo
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Démonstration avec données mockées (pas de backend requis)
              </p>
            </div>
            <div className="bg-yellow-100 border border-yellow-400 rounded-md px-4 py-2">
              <p className="text-sm text-yellow-800 font-medium">
                🧪 Mode Démo - Données Fictives
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Info banner */}
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Comment utiliser cette démo
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>Cliquez sur une session pour ouvrir l'éditeur</li>
                  <li>Utilisez les boutons de navigation pour changer de semaine</li>
                  <li>Les zones vertes représentent les disponibilités</li>
                  <li>Les zones rouges représentent les contraintes (créneaux interdits)</li>
                  <li>Chaque couleur représente une matière différente</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Calendar */}
        <WeeklyCalendarView
          sessions={mockSessions}
          availabilities={mockAvailabilities}
          constraints={mockConstraints}
          onSessionClick={handleSessionClick}
        />

        {/* Statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total d'heures</p>
                <p className="text-2xl font-semibold text-gray-900">15.5h</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Sessions</p>
                <p className="text-2xl font-semibold text-gray-900">{mockSessions.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-100 rounded-md p-3">
                <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Matières</p>
                <p className="text-2xl font-semibold text-gray-900">4</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-100 rounded-md p-3">
                <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Contraintes</p>
                <p className="text-2xl font-semibold text-gray-900">{mockConstraints.length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Légende</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {mockSubjects.map((subject, index) => {
              const colors = [
                'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500',
                'bg-yellow-500', 'bg-indigo-500', 'bg-red-500', 'bg-teal-500'
              ];
              return (
                <div key={subject.id} className="flex items-center">
                  <div className={`w-4 h-4 ${colors[index % colors.length]} rounded mr-2`}></div>
                  <span className="text-sm text-gray-700">{subject.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Session Editor Modal */}
      <SessionEditor
        session={selectedSession}
        subjects={mockSubjects}
        onSave={handleSaveSession}
        onDelete={handleDeleteSession}
        onClose={handleCloseEditor}
        isOpen={isEditorOpen}
      />
    </div>
  );
};

export default CalendarDemo;
