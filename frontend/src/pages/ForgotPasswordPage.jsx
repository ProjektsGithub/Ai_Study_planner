import { useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';

const ForgotPasswordPage = () => {
  const { t } = useLanguage();
  const [email, setEmail] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) { setError('Veuillez entrer votre adresse email.'); return; }
    if (!/\S+@\S+\.\S+/.test(email)) { setError('Adresse email invalide.'); return; }

    setLoading(true);
    setError(null);
    try {
      await apiClient.post('/api/v1/auth/forgot-password', { email });
      setSubmitted(true);
    } catch {
      // On affiche quand même le message de succès pour ne pas révéler si l'email existe
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 py-16">
      {/* Ambient glow orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-violet-600/20 blur-[100px] animate-pulse-slow" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-indigo-600/20 blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full bg-cyan-600/10 blur-[80px]" />
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        <div className="glass-strong rounded-2xl p-8 shadow-glass border border-white/10">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-500 shadow-glow-violet mb-5 animate-float">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">{t('auth.forgot_pwd_title')}</h1>
            <p className="text-sm text-white/50">
              {t('auth.forgot_pwd_desc')}
            </p>
          </div>

          {submitted ? (
            /* ── État succès ── */
            <div className="text-center space-y-6">
              <div className="w-16 h-16 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold text-white mb-2">{t('auth.forgot_pwd_check_mail_title')}</h2>
                <p className="text-sm text-white/55 leading-relaxed">
                  {t('auth.forgot_pwd_check_mail_desc', { email })}
                </p>
              </div>
              <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 text-left">
                <p className="text-xs text-amber-300/80 leading-relaxed">
                  {t('auth.forgot_pwd_expire_note')}
                </p>
              </div>
              <Link
                to="/login"
                className="block text-center text-sm text-violet-400 hover:text-violet-300 transition-colors font-medium"
              >
                ← {t('auth.back_to_login')}
              </Link>
            </div>
          ) : (
            /* ── Formulaire ── */
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label={t('auth.email')}
                type="email"
                name="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(null); }}
                placeholder={t('auth.email_placeholder')}
                error={error}
                required
                autoComplete="email"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                }
              />

              {error && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-3 flex items-center gap-2.5">
                  <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-xs text-red-300">{error}</p>
                </div>
              )}

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full justify-center"
                  loading={loading}
                  disabled={loading}
                >
                  {t('auth.send_reset_link')}
                </Button>
              </div>

              <div className="text-center pt-2">
                <Link
                  to="/login"
                  className="text-xs text-white/50 hover:text-white/80 transition-colors inline-flex items-center gap-1"
                >
                  ← {t('auth.back_to_login')}
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
