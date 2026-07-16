/**
 * CalendarExportMenu — Menu dropdown pour exporter le planning vers un calendrier
 * Options : télécharger .ics | ouvrir dans Google Calendar
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

/**
 * @param {{ planId: number|string, sessions: Array, disabled?: boolean }} props
 */
const CalendarExportMenu = ({ planId, sessions = [], disabled = false }) => {
  const [open, setOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);
  const menuRef = useRef(null);

  // Fermer le menu si on clique à l'extérieur
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Téléchargement .ics
  const handleDownloadIcs = useCallback(async () => {
    if (!planId) return;
    setDownloading(true);
    setError(null);
    try {
      const response = await apiClient.get(
        `/api/v1/calendar/plans/${planId}/ics`,
        { responseType: 'blob' }
      );
      const blob = new Blob([response.data], { type: 'text/calendar' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `plan_etude_${planId}.ics`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch (err) {
      setError('Erreur lors de la génération du fichier .ics');
    } finally {
      setDownloading(false);
    }
  }, [planId]);

  // Deep-link Google Calendar (première session seulement pour démonstration)
  const handleOpenGoogleCalendar = useCallback(() => {
    if (!sessions || sessions.length === 0) return;

    // On ouvre Google Calendar avec la première session comme exemple
    const first = sessions[0];
    const title = encodeURIComponent(
      `${first.subject?.name || 'Étude'} — ${first.task_type || 'Session'}`
    );
    const desc = encodeURIComponent(
      `Plan d'étude AI — ${first.subject?.name || ''} (${first.task_type || ''})`
    );

    // Format dates pour Google Calendar: YYYYMMDDTHHmmss
    const now = new Date();
    const [sh, sm] = (first.start_time || '09:00').split(':').map(Number);
    const [eh, em] = (first.end_time || '10:00').split(':').map(Number);

    const pad = (n) => String(n).padStart(2, '0');
    const dateStr = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
    const startStr = `${dateStr}T${pad(sh)}${pad(sm)}00`;
    const endStr   = `${dateStr}T${pad(eh)}${pad(em)}00`;

    const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startStr}/${endStr}&details=${desc}`;
    window.open(url, '_blank', 'noopener,noreferrer');
    setOpen(false);
  }, [sessions]);

  return (
    <div ref={menuRef} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Trigger button */}
      <button
        id="calendar-export-btn"
        onClick={() => setOpen((v) => !v)}
        disabled={disabled || !planId}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 16px',
          borderRadius: 10,
          border: '1px solid rgba(99,102,241,0.35)',
          background: open
            ? 'rgba(99,102,241,0.2)'
            : 'rgba(99,102,241,0.08)',
          color: disabled || !planId ? 'rgba(255,255,255,0.25)' : '#a5b4fc',
          fontSize: 13,
          fontWeight: 600,
          cursor: disabled || !planId ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          whiteSpace: 'nowrap',
        }}
        onMouseEnter={(e) => {
          if (!disabled && planId) e.currentTarget.style.background = 'rgba(99,102,241,0.18)';
        }}
        onMouseLeave={(e) => {
          if (!open) e.currentTarget.style.background = 'rgba(99,102,241,0.08)';
        }}
      >
        {/* Calendar icon */}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        Calendrier
        {/* Chevron */}
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {open && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            zIndex: 500,
            minWidth: 220,
            background: 'rgba(15,15,30,0.97)',
            border: '1px solid rgba(99,102,241,0.25)',
            borderRadius: 14,
            boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)',
            backdropFilter: 'blur(20px)',
            padding: '6px',
            animation: 'dropdownIn 0.15s ease',
          }}
        >
          <style>{`
            @keyframes dropdownIn {
              from { opacity: 0; transform: translateY(-6px) scale(0.97); }
              to   { opacity: 1; transform: translateY(0) scale(1); }
            }
          `}</style>

          {/* Télécharger .ics */}
          <button
            id="calendar-download-ics-btn"
            onClick={handleDownloadIcs}
            disabled={downloading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              width: '100%',
              padding: '10px 12px',
              borderRadius: 10,
              border: 'none',
              background: 'transparent',
              color: 'rgba(255,255,255,0.85)',
              fontSize: 13,
              fontWeight: 500,
              cursor: downloading ? 'wait' : 'pointer',
              textAlign: 'left',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(99,102,241,0.15)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          >
            {downloading ? (
              <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <span style={{ fontSize: 16 }}>📥</span>
            )}
            <div>
              <div style={{ fontWeight: 600, marginBottom: 1 }}>Télécharger .ics</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                Apple, Outlook, Thunderbird…
              </div>
            </div>
          </button>

          {/* Séparateur */}
          <div style={{ height: 1, background: 'rgba(255,255,255,0.07)', margin: '4px 6px' }} />

          {/* Google Calendar deep-link */}
          <button
            id="calendar-open-google-btn"
            onClick={handleOpenGoogleCalendar}
            disabled={!sessions || sessions.length === 0}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              width: '100%',
              padding: '10px 12px',
              borderRadius: 10,
              border: 'none',
              background: 'transparent',
              color: sessions?.length ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.3)',
              fontSize: 13,
              fontWeight: 500,
              cursor: sessions?.length ? 'pointer' : 'not-allowed',
              textAlign: 'left',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => {
              if (sessions?.length) e.currentTarget.style.background = 'rgba(99,102,241,0.15)';
            }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          >
            {/* Google Calendar logo (coloré) */}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="4" width="18" height="18" rx="2" fill="#4285F4" opacity="0.2" />
              <rect x="3" y="4" width="18" height="18" rx="2" stroke="#4285F4" strokeWidth="1.5" />
              <line x1="3" y1="10" x2="21" y2="10" stroke="#4285F4" strokeWidth="1.5" />
              <line x1="8" y1="2" x2="8" y2="6" stroke="#EA4335" strokeWidth="2" strokeLinecap="round" />
              <line x1="16" y1="2" x2="16" y2="6" stroke="#EA4335" strokeWidth="2" strokeLinecap="round" />
              <text x="12" y="19" fontSize="7" fill="#34A853" fontWeight="bold" textAnchor="middle">G</text>
            </svg>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 1 }}>Ouvrir dans Google Calendar</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                Ajouter la 1ère session
              </div>
            </div>
          </button>

          {/* Message d'erreur */}
          {error && (
            <div style={{
              margin: '6px 6px 2px',
              padding: '8px 10px',
              borderRadius: 8,
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.25)',
              color: '#fca5a5',
              fontSize: 11,
            }}>
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CalendarExportMenu;
