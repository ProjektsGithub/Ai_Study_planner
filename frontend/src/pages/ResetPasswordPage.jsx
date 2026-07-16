import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../api/client';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [formData, setFormData] = useState({ new_password: '', confirm_password: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Rediriger si pas de token dans l'URL
  useEffect(() => {
    if (!token) navigate('/forgot-password', { replace: true });
  }, [token, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.new_password) {
      newErrors.new_password = 'Nouveau mot de passe requis';
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = 'Le mot de passe doit contenir au moins 8 caractères';
    }
    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Veuillez confirmer le mot de passe';
    } else if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Les mots de passe ne correspondent pas';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setErrors({});
    try {
      await apiClient.post('/api/v1/auth/reset-password', {
        token,
        new_password: formData.new_password,
      });
      setSuccess(true);
      // Rediriger vers login après 3 secondes
      setTimeout(() => navigate('/login', { replace: true }), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrors({
        submit: typeof detail === 'string' ? detail : 'Erreur lors de la réinitialisation. Le lien est peut-être expiré.',
      });
    } finally {
      setLoading(false);
    }
  };

  // Indicateur de force du mot de passe
  const getPasswordStrength = (pwd) => {
    if (!pwd) return { score: 0, label: '', color: 'transparent' };
    let score = 0;
    if (pwd.length >= 8)  score++;
    if (pwd.length >= 12) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    if (score <= 1) return { score, label: 'Très faible', color: '#ef4444' };
    if (score === 2) return { score, label: 'Faible', color: '#f97316' };
    if (score === 3) return { score, label: 'Moyen', color: '#eab308' };
    if (score === 4) return { score, label: 'Fort', color: '#22c55e' };
    return { score, label: 'Très fort', color: '#10b981' };
  };

  const strength = getPasswordStrength(formData.new_password);

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
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-500 shadow-glow-violet mb-5 animate-float">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">Nouveau mot de passe</h1>
            <p className="text-sm text-white/50">
              Choisissez un mot de passe sécurisé pour votre compte.
            </p>
          </div>

          {success ? (
            /* ── État succès ── */
            <div className="text-center space-y-6">
              <div className="w-16 h-16 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold text-white mb-2">Mot de passe mis à jour !</h2>
                <p className="text-sm text-white/55 leading-relaxed">
                  Votre mot de passe a été réinitialisé avec succès.
                  Vous allez être redirigé vers la page de connexion…
                </p>
              </div>
              <div className="flex gap-2 justify-center">
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: '#818cf8',
                    animation: `bounce 1.2s ease-in-out infinite`,
                    animationDelay: `${i * 0.2}s`,
                  }} />
                ))}
              </div>
              <Link
                to="/login"
                className="block text-center text-sm text-violet-400 hover:text-violet-300 transition-colors font-medium"
              >
                Aller à la connexion →
              </Link>
              <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}`}</style>
            </div>
          ) : (
            /* ── Formulaire ── */
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Input
                  label="Nouveau mot de passe"
                  type="password"
                  name="new_password"
                  value={formData.new_password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  error={errors.new_password}
                  required
                  autoComplete="new-password"
                  icon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  }
                />
                {/* Indicateur de force */}
                {formData.new_password && (
                  <div className="mt-2 space-y-1">
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((lvl) => (
                        <div
                          key={lvl}
                          style={{
                            flex: 1, height: 3, borderRadius: 4,
                            background: lvl <= strength.score ? strength.color : 'rgba(255,255,255,0.1)',
                            transition: 'background 0.3s',
                          }}
                        />
                      ))}
                    </div>
                    <p style={{ fontSize: 11, color: strength.color }}>{strength.label}</p>
                  </div>
                )}
              </div>

              <Input
                label="Confirmer le mot de passe"
                type="password"
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                placeholder="••••••••"
                error={errors.confirm_password}
                required
                autoComplete="new-password"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                }
              />

              {/* Erreur générale */}
              {errors.submit && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-3.5 flex items-start gap-3">
                  <svg className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-red-300">{errors.submit}</p>
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
                  Réinitialiser le mot de passe
                </Button>
              </div>

              <p className="text-center text-sm text-white/50 pt-1">
                <Link to="/login" className="text-violet-400 hover:text-violet-300 font-medium transition-colors">
                  ← Retour à la connexion
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
