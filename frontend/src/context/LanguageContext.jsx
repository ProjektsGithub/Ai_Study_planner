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
  fr: {
    // Navigation / Sidebar
    'nav.dashboard': 'Tableau de bord',
    'nav.universities': 'Universités',
    'nav.programs': 'Programmes d\'études',
    'nav.tracks': 'Parcours académiques',
    'nav.rules': 'Règles de validation',
    'nav.semesters': 'Semestres',
    'nav.units': 'Unités d\'enseignement',
    'nav.courses': 'Cours',
    'nav.imports': 'Importation en masse',
    'nav.reports': 'Rapports & Exports',
    'nav.audit': 'Journaux d\'audit',
    'nav.roles': 'Gestion des rôles',
    'nav.settings': 'Paramètres système',
    'nav.student_portal': 'Portail étudiant',
    'nav.my_profile': 'Mon profil',
    'nav.preferences': 'Préférences',
    'nav.logout': 'Déconnexion',
    'nav.group.overview': 'Aperçu',
    'nav.group.planning': 'Planification',
    'nav.group.settings': 'Paramètres',
    'nav.group.account': 'Compte',
    'nav.create_plan': 'Créer un plan',
    'nav.my_study_plans': 'Mes plans d\'études',
    'nav.manage_courses': 'Gérer les cours',
    'nav.availabilities': 'Disponibilités',
    'nav.off_days': 'Jours de repos',
    'nav.recommendations': 'Recommandations',
    'nav.logo_subtitle': "Votre planificateur d'études personnalisé",
    'study_tip.title': "Astuce d'étude",
    'study_tip.content': "Essayez la méthode Pomodoro : 25 minutes de révision intense, puis 5 minutes de pause pour rester concentré !",

    // Buttons / Actions
    'action.add': 'Ajouter',
    'action.edit': 'Modifier',
    'action.delete': 'Supprimer',
    'action.save': 'Enregistrer',
    'action.cancel': 'Annuler',
    'action.reset': 'Réinitialiser',
    'action.reload': 'Recharger',
    'action.import': 'Importer',
    'action.export': 'Exporter',
    'action.rollback': 'Restaurer',
    'action.details': 'Détails',

    // Common labels
    'label.search': 'Rechercher...',
    'label.name': 'Nom',
    'label.description': 'Description',
    'label.country': 'Pays',
    'label.ects': 'ECTS',
    'label.level': 'Niveau',
    'label.semester': 'Semestre',
    'label.actions': 'Actions',
    'label.timestamp': 'Horodatage',
    'label.user': 'Utilisateur',
    'label.operation': 'Opération',
    'label.status': 'Statut',

    // UI headers & details
    'admin.platform': 'Plateforme d\'administration',
    'shortcut.legend': 'Raccourcis clavier',
    'error.404.title': 'Page non trouvée',
    'error.404.subtitle': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
    'error.403.title': 'Accès refusé',
    'error.403.subtitle': 'Vous n\'avez pas les permissions requises pour accéder à cette page.',
    'error.back_home': 'Retour à l\'accueil',
  },
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
    'nav.preferences': 'Einstellungen',
    'nav.logout': 'Abmelden',
    'nav.group.overview': 'Übersicht',
    'nav.group.planning': 'Planung',
    'nav.group.settings': 'Einstellungen',
    'nav.group.account': 'Konto',
    'nav.create_plan': 'Studienplan erstellen',
    'nav.my_study_plans': 'Meine Studienpläne',
    'nav.manage_courses': 'Kurse verwalten',
    'nav.availabilities': 'Verfügbarkeiten',
    'nav.off_days': 'Freie Tage',
    'nav.recommendations': 'Empfehlungen',
    'nav.logo_subtitle': "Ihr persönlicher Studienplaner",
    'study_tip.title': "Studientipp",
    'study_tip.content': "Probieren Sie die Pomodoro-Technik aus: 25 Minuten intensiv lernen, dann 5 Minuten Pause machen, um konzentriert zu bleiben!",

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
    'nav.preferences': 'Preferences',
    'nav.logout': 'Logout',
    'nav.group.overview': 'Overview',
    'nav.group.planning': 'Planning',
    'nav.group.settings': 'Settings',
    'nav.group.account': 'Account',
    'nav.create_plan': 'Create a Plan',
    'nav.my_study_plans': 'My Study Plans',
    'nav.manage_courses': 'Manage Courses',
    'nav.availabilities': 'Availabilities',
    'nav.off_days': 'Off Days',
    'nav.recommendations': 'Recommendations',
    'nav.logo_subtitle': "Your personalized study planner",
    'study_tip.title': "Study Tip",
    'study_tip.content': "Try the Pomodoro technique: study intensely for 25 minutes, then take a 5-minute break to stay focused!",

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
  // English is the primary language, German/French secondary
  const [lang, setLang] = useState(() => localStorage.getItem('ui_lang') || 'en');

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ui_lang', newLang);
  };

  const t = (key) => {
    return translations[lang]?.[key] || translations['en']?.[key] || key;
  };

  const getLocalizedName = (entity) => {
    if (!entity) return '';
    if (lang === 'de') return entity.name_de || entity.name;
    if (lang === 'fr') return entity.name_fr || entity.name || entity.name_de;
    return entity.name || entity.name_de || '';
  };

  const getLocalizedDescription = (entity) => {
    if (!entity) return '';
    if (lang === 'de') return entity.description_de || entity.description;
    if (lang === 'fr') return entity.description_fr || entity.description || entity.description_de;
    return entity.description || entity.description_de || '';
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
