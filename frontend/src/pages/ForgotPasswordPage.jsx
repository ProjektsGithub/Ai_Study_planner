import { useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';

const ForgotPasswordPage = () => {
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
            <h1 className="text-2xl font-bold text-white mb-1">Mot de passe oublié ?</h1>
            <p className="text-sm text-white/50">
              Entrez votre email pour recevoir un lien de réinitialisation.
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
                <h2 className="text-lg font-bold text-white mb-2">Vérifiez votre boîte mail</h2>
                <p className="text-sm text-white/55 leading-relaxed">
                  Si l'adresse <span className="text-violet-300 font-medium">{email}</span> est
                  associée à un compte, vous recevrez un lien de réinitialisation dans quelques
                  minutes. Vérifiez également vos spams.
                </p>
              </div>
              <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 text-left">
                <p className="text-xs text-amber-300/80 leading-relaxed">
                  ⏱ Le lien expire après <strong>1 heure</strong>. Si vous ne le recevez pas,
                  vous pouvez refaire une demande.
                </p>
              </div>
              <Link
                to="/login"
                className="block text-center text-sm text-violet-400 hover:text-violet-300 transition-colors font-medium"
              >
                ← Retour à la connexion
              </Link>
            </div>
          ) : (
            /* ── Formulaire ── */
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Adresse email"
                type="email"
                name="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(null); }}
                placeholder="vous@exemple.com"
                error={error}
                required
                autoComplete="email"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                }
              />

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full justify-center"
                  loading={loading}
                  disabled={loading}
                >
                  Envoyer le lien de réinitialisation
                </Button>
              </div>

              <p className="text-center text-sm text-white/50 pt-1">
                Vous vous souvenez ?{' '}
                <Link to="/login" className="text-violet-400 hover:text-violet-300 font-medium transition-colors">
                  Se connecter
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
