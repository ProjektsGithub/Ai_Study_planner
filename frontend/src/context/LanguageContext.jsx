import { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import fr from '../locales/fr';
import en from '../locales/en';
import de from '../locales/de';

const LanguageContext = createContext(null);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};

const translations = {
  fr,
  en,
  de,
};

export const LanguageProvider = ({ children }) => {
  // English default, or saved user preference
  const [lang, setLang] = useState(() => localStorage.getItem('ui_lang') || 'fr');

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ui_lang', newLang);
  };

  const t = (key, defaultText) => {
    return translations[lang]?.[key] || translations['en']?.[key] || defaultText || key;
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

export default LanguageContext;
