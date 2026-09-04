import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useColabStatus } from '../hooks/useColabStatus';
import { useLanguage } from '../context/LanguageContext';

/**
 * ColabStatusBadge
 * Displays real-time availability of the Google Colab / AI backend.
 * Variants:
 *  - "badge": Pill badge with dot, status text, latency, and click-to-open details modal (ideal for page headers).
 *  - "header": Subtle compact pill for the top navigation bar.
 *  - "dot": Minimal pulsing indicator dot with hover/click tooltip (ideal for ChatBot header).
 *  - "panel": Full embedded status card with diagnostics and refresh button (ideal for planner page).
 */
const ColabStatusBadge = ({ variant = 'badge', className = '', showRefresh = true }) => {
  const { ok, backend, configured, url, latency_ms, model, gpu, device, error, lastChecked, isFetching, refresh } = useColabStatus();
  const { t } = useLanguage();
  const [modalOpen, setModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const popoverRef = useRef(null);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setModalOpen(false);
      }
    };
    if (modalOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [modalOpen]);

  const isOnline = ok === true;
  const isOffline = ok === false;
  const isChecking = isFetching;
  const isUnconfigured = configured === false;

  // Status visual attributes
  let dotColor = '#94a3b8'; // slate
  let dotGlow = 'rgba(148, 163, 184, 0.4)';
  let statusText = t('colab.checking', 'Vérification...');
  let badgeBg = 'rgba(148, 163, 184, 0.12)';
  let badgeBorder = 'rgba(148, 163, 184, 0.25)';
  let textColor = '#cbd5e1';

  if (isChecking && ok === null) {
    dotColor = '#fbbf24'; // amber
    dotGlow = 'rgba(251, 191, 36, 0.6)';
    statusText = t('colab.connecting', 'Connexion...');
    badgeBg = 'rgba(251, 191, 36, 0.12)';
    badgeBorder = 'rgba(251, 191, 36, 0.3)';
    textColor = '#fde68a';
  } else if (isUnconfigured) {
    dotColor = '#94a3b8';
    dotGlow = 'rgba(148, 163, 184, 0.3)';
    statusText = t('colab.unconfigured', 'Non configuré');
    badgeBg = 'rgba(148, 163, 184, 0.12)';
    badgeBorder = 'rgba(148, 163, 184, 0.25)';
    textColor = '#cbd5e1';
  } else if (isOnline) {
    dotColor = '#10b981'; // emerald
    dotGlow = 'rgba(16, 185, 129, 0.6)';
    statusText = backend === 'colab' ? t('colab.connected', 'Colab connecté') : t('colab.local_ready', 'IA Locale prête');
    badgeBg = 'rgba(16, 185, 129, 0.12)';
    badgeBorder = 'rgba(16, 185, 129, 0.3)';
    textColor = '#6ee7b7';
  } else if (isOffline) {
    dotColor = '#ef4444'; // red
    dotGlow = 'rgba(239, 68, 68, 0.6)';
    statusText = backend === 'colab' ? t('colab.disconnected', 'Colab déconnecté') : t('colab.local_offline', 'IA Locale hors ligne');
    badgeBg = 'rgba(239, 68, 68, 0.12)';
    badgeBorder = 'rgba(239, 68, 68, 0.3)';
    textColor = '#fca5a5';
  }

  const handleCopyUrl = () => {
    if (url) {
      navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // ── VARIANT: MINIMAL DOT (For ChatBot header) ─────────────────────────────
  if (variant === 'dot') {
    return (
      <div className="relative inline-flex items-center" title={`${statusText}${latency_ms ? ` (${latency_ms}ms)` : ''}`}>
        <button
          type="button"
          onClick={() => setModalOpen(!modalOpen)}
          className="relative flex items-center justify-center p-1 rounded-full hover:bg-white/10 transition-colors focus:outline-none"
          aria-label="Statut du serveur Colab"
        >
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: '50%',
              backgroundColor: dotColor,
              boxShadow: `0 0 8px ${dotGlow}`,
              display: 'inline-block',
              animation: isOnline || isChecking ? 'colabPulse 2s infinite' : 'none',
            }}
          />
        </button>

        {/* Mini tooltip modal when clicked */}
        {modalOpen && (
          <div
            ref={popoverRef}
            style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: 8,
              zIndex: 10000,
              width: 280,
              backgroundColor: '#1e1b4b',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: 14,
              padding: 14,
              boxShadow: '0 12px 36px rgba(0,0,0,0.4)',
              color: '#fff',
              fontSize: 12,
            }}
          >
            <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-2.5">
              <span className="font-semibold text-white flex items-center gap-1.5">
                <span>⚡</span> {t('colab.backend_type', 'Backend Type')} : {backend === 'colab' ? 'Google Colab' : 'Ollama'}
              </span>
              <span
                className="px-2 py-0.5 rounded text-[11px] font-medium"
                style={{ backgroundColor: badgeBg, color: textColor, border: `1px solid ${badgeBorder}` }}
              >
                {statusText}
              </span>
            </div>

            <div className="space-y-1.5 text-slate-300 text-[11.5px] mb-3">
              {model && <div><span className="text-slate-400">{t('colab.model', 'Modèle')}:</span> {model}</div>}
              {gpu && <div><span className="text-slate-400">{t('colab.gpu', 'GPU')}:</span> {gpu}</div>}
              {latency_ms !== null && <div><span className="text-slate-400">{t('colab.latency', 'Latence')}:</span> {latency_ms} ms</div>}
              {error && <div className="text-red-300 text-[11px] mt-1 leading-snug">{error}</div>}
            </div>

            <div className="flex items-center justify-between pt-1 border-t border-white/10">
              <span className="text-[10.5px] text-slate-400">
                {lastChecked ? `${t('colab.last_check', 'Dernier check')}: ${lastChecked.toLocaleTimeString()}` : ''}
              </span>
              <button
                type="button"
                onClick={() => refresh()}
                disabled={isChecking}
                className="px-2.5 py-1 text-[11px] bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white rounded-md font-medium transition-colors flex items-center gap-1"
              >
                <span className={isChecking ? 'animate-spin' : ''}>↻</span> {t('action.test_connection', 'Tester')}
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── VARIANT: EMBEDDED PANEL (For AIPlanPage) ──────────────────────────────
  if (variant === 'panel') {
    return (
      <div
        className={`rounded-2xl p-5 backdrop-blur-md transition-all duration-300 ${className}`}
        style={{
          backgroundColor: isOnline ? 'rgba(16, 185, 129, 0.04)' : isOffline ? 'rgba(239, 68, 68, 0.05)' : 'rgba(255, 255, 255, 0.03)',
          border: `1px solid ${isOnline ? 'rgba(16, 185, 129, 0.2)' : isOffline ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255, 255, 255, 0.08)'}`,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.06)',
        }}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            {/* Status icon with pulse glow */}
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: isOnline
                  ? 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.3))'
                  : isOffline
                  ? 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(185,28,28,0.3))'
                  : 'linear-gradient(135deg, rgba(251,191,36,0.2), rgba(217,119,6,0.3))',
                border: `1px solid ${badgeBorder}`,
              }}
            >
              <span className="text-xl">
                {isOnline ? '🚀' : isOffline ? '🔌' : '⏳'}
              </span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white">
                  {t('colab.badge_title', 'Serveur de calcul IA — Google Colab')}
                </h3>
                <span
                  className="px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1.5"
                  style={{ backgroundColor: badgeBg, color: textColor, border: `1px solid ${badgeBorder}` }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      backgroundColor: dotColor,
                      boxShadow: `0 0 6px ${dotGlow}`,
                      animation: isOnline ? 'colabPulse 2s infinite' : 'none',
                    }}
                  />
                  {statusText}
                </span>
              </div>

              <p className="text-xs text-white/50 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                {gpu && <span>{t('colab.gpu', 'GPU')}: <strong className="text-white/80">{gpu}</strong></span>}
                {model && <span>{t('colab.model', 'Modèle')}: <strong className="text-white/80">{model}</strong></span>}
                {latency_ms !== null && (
                  <span>
                    {t('colab.latency', 'Latence')}: <strong className={latency_ms < 300 ? 'text-emerald-400' : 'text-amber-400'}>{latency_ms} ms</strong>
                  </span>
                )}
                {lastChecked && (
                  <span className="text-white/30">
                    {t('colab.last_check', 'Dernier check')}: {lastChecked.toLocaleTimeString()}
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              type="button"
              onClick={() => refresh()}
              disabled={isChecking}
              className="px-3 py-1.5 rounded-xl text-xs font-medium text-white/80 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50"
            >
              <svg
                className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{isChecking ? t('colab.checking', 'Vérification...') : t('action.test_connection', 'Tester la connexion')}</span>
            </button>
          </div>
        </div>

        {/* Offline troubleshooting banner */}
        {isOffline && (
          <div className="mt-4 pt-3.5 border-t border-red-500/20 text-xs text-red-200/90 leading-relaxed">
            <div className="font-semibold text-red-300 mb-1.5 flex items-center gap-1.5">
              <span>⚠️</span> {t('colab.disconnected', 'Colab déconnecté')}
            </div>
            {error && <p className="mb-2 text-red-300/80 font-mono text-[11px]">{error}</p>}
            <div className="bg-red-950/40 rounded-lg p-2.5 border border-red-500/20 text-[11px] space-y-1">
              <p className="font-medium text-red-200">{t('colab.troubleshooting', 'Conseils de dépannage')} :</p>
              <ol className="list-decimal list-inside space-y-0.5 text-red-200/80 pl-1">
                <li>{t('colab.tip_1', 'Vérifiez que le notebook Colab est bien exécuté et connecté au GPU.')}</li>
                <li>{t('colab.tip_2', 'Vérifiez que le tunnel Ngrok / Cloudflare est actif dans le fichier backend .env.')}</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── VARIANT: BADGE (Header / Pill with Modal) ─────────────────────────────
  return (
    <div className={`relative inline-block ${className}`}>
      {/* Pulse keyframes */}
      <style>{`
        @keyframes colabPulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.3); opacity: 0.7; }
        }
      `}</style>

      {/* Clickable Badge Pill */}
      <button
        type="button"
        id="colab-status-badge"
        onClick={() => setModalOpen(!modalOpen)}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-sm transition-all duration-200 hover:scale-[1.02] focus:outline-none cursor-pointer"
        style={{
          backgroundColor: badgeBg,
          border: `1px solid ${badgeBorder}`,
          color: textColor,
          boxShadow: `0 2px 10px ${dotGlow}`,
        }}
        title="Cliquer pour afficher l'état détaillé du serveur Colab"
      >
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            backgroundColor: dotColor,
            boxShadow: `0 0 6px ${dotGlow}`,
            animation: isOnline || isChecking ? 'colabPulse 2s infinite' : 'none',
          }}
        />
        <span className="font-semibold tracking-wide">
          {backend === 'colab' ? 'Colab' : 'Ollama'}:
        </span>
        <span>{statusText}</span>

        {latency_ms !== null && isOnline && (
          <span className="opacity-75 text-[11px] font-mono ml-0.5">
            ({latency_ms}ms)
          </span>
        )}

        <svg
          className={`w-3 h-3 transition-transform ${modalOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Detailed Diagnostics Popover / Dropdown Modal */}
      {modalOpen && (
        <div
          ref={popoverRef}
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            zIndex: 9999,
            width: 340,
            backgroundColor: '#0f172a',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 18,
            padding: '18px 20px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
            color: '#f8fafc',
            animation: 'fadeIn 0.2s ease-out',
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3.5">
            <div className="flex items-center gap-2">
              <span className="text-lg">🤖</span>
              <div>
                <h4 className="font-bold text-white text-sm">{t('colab.diagnostic_title', 'Disponibilité Serveur IA')}</h4>
                <p className="text-[11px] text-white/50">
                  {t('colab.backend_type', 'Backend')}: {backend === 'colab' ? 'Google Colab (Cloud GPU)' : 'Ollama (Local)'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="text-white/40 hover:text-white text-sm p-1 rounded-md transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Status highlight pill */}
          <div
            className="flex items-center justify-between p-3 rounded-xl mb-3"
            style={{
              backgroundColor: badgeBg,
              border: `1px solid ${badgeBorder}`,
            }}
          >
            <div className="flex items-center gap-2">
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: dotColor,
                  boxShadow: `0 0 8px ${dotGlow}`,
                  display: 'inline-block',
                }}
              />
              <span className="font-semibold text-sm" style={{ color: textColor }}>
                {statusText}
              </span>
            </div>
            {latency_ms !== null && (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-black/20" style={{ color: textColor }}>
                {latency_ms} ms
              </span>
            )}
          </div>

          {/* Diagnostic Metrics Grid */}
          <div className="space-y-2 text-xs mb-4">
            <div className="flex justify-between py-1 border-b border-white/5">
              <span className="text-white/50">{t('colab.model', 'Modèle')}</span>
              <span className="text-white font-medium">{model || 'Llama-3.1-8B-Instruct'}</span>
            </div>

            {gpu && (
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-white/50">{t('colab.gpu', 'GPU')}</span>
                <span className="text-emerald-400 font-medium">{gpu}</span>
              </div>
            )}

            {device && (
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-white/50">{t('colab.device', 'Périphérique')}</span>
                <span className="text-white font-mono uppercase text-[11px]">{device}</span>
              </div>
            )}

            {url && (
              <div className="flex justify-between items-center py-1 border-b border-white/5">
                <span className="text-white/50">{t('colab.api_url', 'URL Endpoint')}</span>
                <button
                  type="button"
                  onClick={handleCopyUrl}
                  className="text-violet-400 hover:text-violet-300 font-mono text-[11px] truncate max-w-[170px]"
                  title={t('colab.copy_url', 'Cliquer pour copier l\'URL')}
                >
                  {copied ? `✅ ${t('colab.copied', 'Copié !')}` : url.replace(/^https?:\/\//, '')}
                </button>
              </div>
            )}

            {lastChecked && (
              <div className="flex justify-between py-1">
                <span className="text-white/50">{t('colab.last_check', 'Dernier test')}</span>
                <span className="text-white/70">{lastChecked.toLocaleTimeString()}</span>
              </div>
            )}
          </div>

          {/* Error explanation if offline */}
          {isOffline && error && (
            <div className="mb-3.5 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-[11px] text-red-300 leading-snug">
              <div className="font-semibold mb-1 flex items-center gap-1">
                <span>⚠️</span> Cause :
              </div>
              <p>{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={() => refresh()}
              disabled={isChecking}
              className="w-full py-2 px-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs transition-all duration-150 flex items-center justify-center gap-2 shadow-lg shadow-violet-600/30 disabled:opacity-50"
            >
              <svg
                className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{isChecking ? t('colab.checking', 'Vérification...') : t('action.test_connection', 'Tester la connexion')}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

ColabStatusBadge.propTypes = {
  variant: PropTypes.oneOf(['badge', 'header', 'dot', 'panel']),
  className: PropTypes.string,
  showRefresh: PropTypes.bool,
};

export default ColabStatusBadge;
