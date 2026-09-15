/**
 * Utility for formatting and simplifying academic course names and session types.
 */

// Common substitutions for long academic terms in French & English
const REPLACEMENTS = [
  // Multi-word French replacements
  { regex: /\bintroduction\s+aux\b/gi, with: 'Intro.' },
  { regex: /\bintroduction\s+au\b/gi, with: 'Intro.' },
  { regex: /\bintroduction\s+à\s+la\b/gi, with: 'Intro.' },
  { regex: /\bintroduction\s+à\b/gi, with: 'Intro.' },
  { regex: /\bintroduction\b/gi, with: 'Intro.' },
  { regex: /\bbases\s+de\s+données\b/gi, with: 'BDD' },
  { regex: /\bbase\s+de\s+données\b/gi, with: 'BDD' },
  { regex: /\bstructures\s+de\s+données\b/gi, with: 'Struct. Données' },
  { regex: /\bsystèmes?\s+d'exploitation\b/gi, with: "Syst. d'Exploit." },
  { regex: /\bprogrammation\s+orientée\s+objet\b/gi, with: 'POO' },
  { regex: /\bintelligence\s+artificielle\b/gi, with: 'IA' },
  { regex: /\bmachine\s+learning\b/gi, with: 'ML' },
  { regex: /\bdeep\s+learning\b/gi, with: 'DL' },
  { regex: /\bgestion\s+de\s+projet\b/gi, with: 'Gestion Projet' },
  { regex: /\bréseaux\s+informatiques\b/gi, with: 'Réseaux' },
  { regex: /\balgorithmique\b/gi, with: 'Algo.' },
  { regex: /\balgorithmes?\b/gi, with: 'Algo.' },
  { regex: /\bmathématiques?\b/gi, with: 'Maths' },
  { regex: /\bstatistiques?\b/gi, with: 'Stats' },
  { regex: /\bprobabilités?\b/gi, with: 'Proba' },
  { regex: /\bprogrammation\b/gi, with: 'Prog.' },
  { regex: /\bdéveloppement\b/gi, with: 'Dév.' },
  { regex: /\barchitecture\b/gi, with: 'Arch.' },
  { regex: /\binformatique\b/gi, with: 'Info.' },
  { regex: /\btechnologies?\b/gi, with: 'Techno.' },
  { regex: /\bcommunication\b/gi, with: 'Com.' },
  { regex: /\bmanagement\b/gi, with: 'Mgmt' },
  { regex: /\bphysique\b/gi, with: 'Phys.' },
  { regex: /\bchimie\b/gi, with: 'Chim.' },
  { regex: /\bélectronique\b/gi, with: 'Électro.' },
  { regex: /\béconomie\b/gi, with: 'Éco.' },
  { regex: /\borganisation\b/gi, with: 'Orga.' },
  { regex: /\benvironnement\b/gi, with: 'Env.' },
  { regex: /\s+et\s+/gi, with: ' & ' },
  { regex: /\s+and\s+/gi, with: ' & ' },
];

/**
 * Simplifies a potentially long course name for compact display in calendar grids.
 * @param {string} name - Raw course or subject name.
 * @param {number} maxLength - Max recommended characters before intelligent truncation (default: 26).
 * @returns {string} Simplified name.
 */
export function simplifyCourseName(name, maxLength = 26) {
  if (!name || typeof name !== 'string') return '';
  const trimmed = name.trim();
  if (trimmed.length <= maxLength) return trimmed;

  let simplified = trimmed;
  for (const { regex, with: replacement } of REPLACEMENTS) {
    simplified = simplified.replace(regex, replacement);
  }

  // Clean up any double spaces
  simplified = simplified.replace(/\s+/g, ' ').trim();

  // If still longer than maxLength, truncate cleanly at word boundary
  if (simplified.length > maxLength) {
    const cut = simplified.slice(0, maxLength);
    const lastSpace = cut.lastIndexOf(' ');
    if (lastSpace > maxLength * 0.5) {
      simplified = cut.slice(0, lastSpace).trim() + '…';
    } else {
      simplified = cut.trim() + '…';
    }
  }

  return simplified;
}

/**
 * Academic session themes and labels configuration.
 */
export const ACADEMIC_TYPES = {
  CM: {
    code: 'CM',
    icon: '🏛️',
    isCourse: true,
    badgeText: 'COURS • CM',
    shortLabel: 'Cours (CM)',
    fullLabel: 'Cours Magistral (CM)',
    theme: {
      solid: '#2563eb', // Royal Blue
      dark: '#1d4ed8',
      lightBg: 'rgba(37, 99, 235, 0.12)',
      textColor: '#ffffff',
      tagColor: 'blue',
    },
  },
  TD: {
    code: 'TD',
    icon: '📝',
    isCourse: true,
    badgeText: 'COURS • TD',
    shortLabel: 'TD (Dirigé)',
    fullLabel: 'Travaux Dirigés (TD)',
    theme: {
      solid: '#7c3aed', // Vibrant Violet
      dark: '#6d28d9',
      lightBg: 'rgba(124, 58, 237, 0.12)',
      textColor: '#ffffff',
      tagColor: 'purple',
    },
  },
  TP: {
    code: 'TP',
    icon: '🧪',
    isCourse: true,
    badgeText: 'COURS • TP',
    shortLabel: 'TP (Pratique)',
    fullLabel: 'Travaux Pratiques (TP)',
    theme: {
      solid: '#059669', // Emerald
      dark: '#047857',
      lightBg: 'rgba(5, 150, 105, 0.12)',
      textColor: '#ffffff',
      tagColor: 'green',
    },
  },
  EXAM: {
    code: 'EXAM',
    icon: '🎯',
    isCourse: true,
    badgeText: 'EXAMEN',
    shortLabel: 'Examen',
    fullLabel: 'Examen / Évaluation',
    theme: {
      solid: '#dc2626', // Red
      dark: '#b91c1c',
      lightBg: 'rgba(220, 38, 38, 0.12)',
      textColor: '#ffffff',
      tagColor: 'red',
    },
  },
};

/**
 * Resolves session details (whether it is an academic course or independent study).
 * @param {object} session
 * @returns {object} enriched metadata
 */
export function getSessionCategoryInfo(session) {
  if (!session) return { isCourse: false, icon: '📖', label: 'Étude' };

  const rawType = (session.session_type || '').toUpperCase().trim();
  const isAcademic =
    Boolean(session.is_academic_fixed) ||
    session.task_type === 'university_class' ||
    ['CM', 'TD', 'TP', 'EXAM'].includes(rawType);

  if (isAcademic) {
    const config = ACADEMIC_TYPES[rawType] || {
      code: rawType || 'COURS',
      icon: '🏛️',
      isCourse: true,
      badgeText: rawType ? `COURS • ${rawType}` : 'COURS UNIV',
      shortLabel: rawType ? `Cours (${rawType})` : 'Cours Univ',
      fullLabel: rawType ? `Cours Universitaire (${rawType})` : 'Cours Universitaire',
      theme: {
        solid: '#2563eb',
        dark: '#1e3a8a',
        lightBg: 'rgba(37, 99, 235, 0.12)',
        textColor: '#ffffff',
        tagColor: 'blue',
      },
    };

    const hasGroup = session.group_name && !['Promotion (Fixe)', 'All'].includes(session.group_name);
    const badgeText = hasGroup ? `${config.code} • ${session.group_name}` : config.badgeText;
    const fullLabel = hasGroup ? `${config.fullLabel} (${session.group_name})` : config.fullLabel;

    return {
      isCourse: true,
      categoryBadge: '🎓 COURS',
      sessionCode: config.code,
      badgeText,
      shortLabel: config.shortLabel,
      fullLabel,
      icon: config.icon,
      solid: config.theme.solid,
      dark: config.theme.dark,
      lightBg: config.theme.lightBg,
      textColor: config.theme.textColor,
      roomLocation: session.room_location || null,
      groupName: session.group_name || null,
    };
  }

  // Personal study sessions
  const studyThemes = {
    lecture_review:    { icon: '📖', label: 'Révision Cours',  short: 'Révision', solid: '#4f46e5', dark: '#3730a3' },
    exercise_practice: { icon: '✏️', label: 'Exercices',       short: 'Exercices', solid: '#ea580c', dark: '#c2410c' },
    exam_preparation:  { icon: '📝', label: 'Prépa Examen',    short: 'Prépa Exam', solid: '#e11d48', dark: '#be123c' },
    project_work:      { icon: '🔧', label: 'Projet',          short: 'Projet', solid: '#0d9488', dark: '#0f766e' },
    reading:           { icon: '📚', label: 'Lecture',         short: 'Lecture', solid: '#0284c7', dark: '#0369a1' },
    practice:          { icon: '🎯', label: 'Pratique',        short: 'Pratique', solid: '#db2777', dark: '#be185d' },
  };

  const key = session.task_type || 'lecture_review';
  const cfg = studyThemes[key] || studyThemes.lecture_review;

  return {
    isCourse: false,
    categoryBadge: '📚 RÉVISION',
    sessionCode: key,
    badgeText: cfg.label,
    shortLabel: cfg.short,
    fullLabel: cfg.label,
    icon: cfg.icon,
    solid: cfg.solid,
    dark: cfg.dark,
    lightBg: 'rgba(99, 102, 241, 0.1)',
    textColor: '#ffffff',
    roomLocation: null,
  };
}
