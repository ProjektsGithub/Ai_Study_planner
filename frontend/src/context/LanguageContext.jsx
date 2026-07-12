import { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';

const LanguageContext = createContext(null);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};

const translations = {
  de: {
    // Navigation / Sidebar
    'nav.dashboard': 'Dashboard',
    'nav.universities': 'Universitäten',
    'nav.programs': 'Studiengänge',
    'nav.tracks': 'Studienrichtungen',
    'nav.rules': 'Validierungsregeln',
    'nav.semesters': 'Semester',
    'nav.units': 'Lerneinheiten',
    'nav.courses': 'Kurse',
    'nav.imports': 'Massenimport',
    'nav.reports': 'Berichte & Exporte',
    'nav.audit': 'Audit-Protokolle',
    'nav.roles': 'Rollenverwaltung',
    'nav.settings': 'Systemeinstellungen',
    'nav.student_portal': 'Studentenportal',
    'nav.my_profile': 'Mein Profil',
    'nav.logout': 'Abmelden',

    // Buttons / Actions
    'action.add': 'Hinzufügen',
    'action.edit': 'Bearbeiten',
    'action.delete': 'Löschen',
    'action.save': 'Speichern',
    'action.cancel': 'Abbrechen',
    'action.reset': 'Zurücksetzen',
    'action.reload': 'Neu laden',
    'action.import': 'Importieren',
    'action.export': 'Exportieren',
    'action.rollback': 'Zurückrollen',
    'action.details': 'Details',

    // Common labels
    'label.search': 'Suchen...',
    'label.name': 'Name',
    'label.description': 'Beschreibung',
    'label.country': 'Land',
    'label.ects': 'ECTS',
    'label.level': 'Ebene',
    'label.semester': 'Semester',
    'label.actions': 'Aktionen',
    'label.timestamp': 'Zeitstempel',
    'label.user': 'Benutzer',
    'label.operation': 'Operation',
    'label.status': 'Status',

    // UI headers & details
    'admin.platform': 'Admin-Plattform',
    'shortcut.legend': 'Tastaturkürzel-Legende',
    'error.404.title': 'Seite nicht gefunden',
    'error.404.subtitle': 'Die gesuchte Seite existiert nicht oder wurde verschoben.',
    'error.403.title': 'Zugriff verweigert',
    'error.403.subtitle': 'Sie haben keine Berechtigung, auf diese Seite zuzugreifen.',
    'error.back_home': 'Zurück zur Startseite',
  },
  en: {
    // Navigation / Sidebar
    'nav.dashboard': 'Dashboard',
    'nav.universities': 'Universities',
    'nav.programs': 'Study Programs',
    'nav.tracks': 'Academic Tracks',
    'nav.rules': 'Validation Rules',
    'nav.semesters': 'Semesters',
    'nav.units': 'Teaching Units',
    'nav.courses': 'Courses',
    'nav.imports': 'Bulk Import',
    'nav.reports': 'Reports & Exports',
    'nav.audit': 'Audit Logs',
    'nav.roles': 'Role Management',
    'nav.settings': 'System Settings',
    'nav.student_portal': 'Student Portal',
    'nav.my_profile': 'My Profile',
    'nav.logout': 'Logout',

    // Buttons / Actions
    'action.add': 'Add',
    'action.edit': 'Edit',
    'action.delete': 'Delete',
    'action.save': 'Save',
    'action.cancel': 'Cancel',
    'action.reset': 'Reset',
    'action.reload': 'Reload',
    'action.import': 'Import',
    'action.export': 'Export',
    'action.rollback': 'Rollback',
    'action.details': 'Details',

    // Common labels
    'label.search': 'Search...',
    'label.name': 'Name',
    'label.description': 'Description',
    'label.country': 'Country',
    'label.ects': 'ECTS',
    'label.level': 'Level',
    'label.semester': 'Semester',
    'label.actions': 'Actions',
    'label.timestamp': 'Timestamp',
    'label.user': 'User',
    'label.operation': 'Operation',
    'label.status': 'Status',

    // UI headers & details
    'admin.platform': 'Admin Platform',
    'shortcut.legend': 'Keyboard Shortcuts Legend',
    'error.404.title': 'Page Not Found',
    'error.404.subtitle': 'The page you are looking for does not exist or has been moved.',
    'error.403.title': 'Access Denied',
    'error.403.subtitle': 'You do not have the required permissions to access this page.',
    'error.back_home': 'Back to Home',
  }
};

export const LanguageProvider = ({ children }) => {
  // German is the primary language (as per Requirement 17.1), English secondary
  const [lang, setLang] = useState(() => localStorage.getItem('ui_lang') || 'de');

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ui_lang', newLang);
  };

  const t = (key) => {
    return translations[lang]?.[key] || translations['de']?.[key] || key;
  };

  const getLocalizedName = (entity) => {
    if (!entity) return '';
    return lang === 'de' ? (entity.name_de || entity.name) : (entity.name || entity.name_de || '');
  };

  const getLocalizedDescription = (entity) => {
    if (!entity) return '';
    return lang === 'de' ? (entity.description_de || entity.description) : (entity.description || entity.description_de || '');
  };

  const formatEuroDate = (date) => {
    if (!date) return '—';
    const d = new Date(date);
    if (isNaN(d.getTime())) return '—';
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}.${month}.${year}`;
  };

  return (
    <LanguageContext.Provider value={{ lang, changeLanguage, t, getLocalizedName, getLocalizedDescription, formatEuroDate }}>
      {children}
    </LanguageContext.Provider>
  );
};

LanguageProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
