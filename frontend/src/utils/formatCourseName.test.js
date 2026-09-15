import { describe, it, expect } from 'vitest';
import { simplifyCourseName, getSessionCategoryInfo, ACADEMIC_TYPES } from './formatCourseName';

describe('formatCourseName utility', () => {
  describe('simplifyCourseName', () => {
    it('returns empty string for null or invalid inputs', () => {
      expect(simplifyCourseName(null)).toBe('');
      expect(simplifyCourseName(undefined)).toBe('');
      expect(simplifyCourseName('')).toBe('');
    });

    it('keeps short course names untouched', () => {
      expect(simplifyCourseName('Mathématiques')).toBe('Mathématiques');
      expect(simplifyCourseName('Physique')).toBe('Physique');
      expect(simplifyCourseName('Anglais')).toBe('Anglais');
    });

    it('simplifies long academic titles with common abbreviations', () => {
      const longTitle = 'Introduction aux bases de données relationnelles';
      const simplified = simplifyCourseName(longTitle, 26);
      expect(simplified).toContain('Intro.');
      expect(simplified).toContain('BDD');
      expect(simplified.length).toBeLessThanOrEqual(28);
    });

    it('simplifies complex names like Algorithmique et structures de données avancées', () => {
      const longTitle = 'Algorithmique et programmation orientée objet avancée';
      const simplified = simplifyCourseName(longTitle, 26);
      expect(simplified).toContain('Algo.');
      expect(simplified).toContain('POO');
    });

    it('truncates cleanly with ellipsis if still too long', () => {
      const veryLong = 'Approfondissement des méthodologies de recherche et développement en biotechnologies';
      const simplified = simplifyCourseName(veryLong, 24);
      expect(simplified.endsWith('…')).toBe(true);
      expect(simplified.length).toBeLessThanOrEqual(26);
    });
  });

  describe('getSessionCategoryInfo', () => {
    it('identifies CM as course with clear label and blue theme', () => {
      const info = getSessionCategoryInfo({ session_type: 'CM', is_academic_fixed: true });
      expect(info.isCourse).toBe(true);
      expect(info.fullLabel).toBe('Cours Magistral (CM)');
      expect(info.badgeText).toBe('COURS • CM');
      expect(info.icon).toBe('🏛️');
      expect(info.solid).toBe('#2563eb');
    });

    it('identifies TP as course with emerald theme and practical label', () => {
      const info = getSessionCategoryInfo({ session_type: 'TP', is_academic_fixed: true });
      expect(info.isCourse).toBe(true);
      expect(info.fullLabel).toBe('Travaux Pratiques (TP)');
      expect(info.badgeText).toBe('COURS • TP');
      expect(info.icon).toBe('🧪');
      expect(info.solid).toBe('#059669');
    });

    it('identifies TD as course with violet theme', () => {
      const info = getSessionCategoryInfo({ session_type: 'TD', is_academic_fixed: true });
      expect(info.isCourse).toBe(true);
      expect(info.fullLabel).toBe('Travaux Dirigés (TD)');
      expect(info.badgeText).toBe('COURS • TD');
      expect(info.icon).toBe('📝');
    });

    it('identifies autonomous study session as non-course', () => {
      const info = getSessionCategoryInfo({ task_type: 'lecture_review' });
      expect(info.isCourse).toBe(false);
      expect(info.fullLabel).toBe('Révision Cours');
      expect(info.categoryBadge).toBe('📚 RÉVISION');
    });
  });
});
