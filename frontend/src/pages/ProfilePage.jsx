import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import apiClient from '../api/client';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const ProfilePage = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [updatingAccount, setUpdatingAccount] = useState(false);
  const [accountMessage, setAccountMessage] = useState(null);

  const [accountData, setAccountData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [updatingPassword, setUpdatingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState(null);
  const [passwordErrors, setPasswordErrors] = useState({});

  // Mock avatar selection
  const [avatarIndex, setAvatarIndex] = useState(() => {
    return parseInt(localStorage.getItem('user_avatar_idx') || '0');
  });

  const avatars = [
    '✦', '🚀', '🧠', '🎓', '🎨', '💻', '⚡', '🌟'
  ];

  useEffect(() => {
    if (user) {
      setAccountData({
        name: user.name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  const handleAccountSubmit = async (e) => {
    e.preventDefault();
    setUpdatingAccount(true);
    setAccountMessage(null);
    try {
      await apiClient.put('/api/v1/auth/update-profile', {
        name: accountData.name,
        email: accountData.email,
      });
      setAccountMessage({ type: 'success', text: t('profile.title', 'Profil') + ' mis à jour !' });
      
      // Update local storage avatar choice
      localStorage.setItem('user_avatar_idx', avatarIndex.toString());
      
      setTimeout(() => {
        window.location.reload();
      }, 1200);
    } catch (err) {
      console.error('Account update error:', err);
      setAccountMessage({ type: 'error', text: err.response?.data?.detail || 'Erreur lors de la mise à jour.' });
    } finally {
      setUpdatingAccount(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordErrors({});
    setPasswordMessage(null);
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordErrors({ confirmPassword: 'Les mots de passe ne correspondent pas' });
      return;
    }
    
    if (passwordData.newPassword.length < 8) {
      setPasswordErrors({ newPassword: 'Au moins 8 caractères requis' });
      return;
    }
    
    setUpdatingPassword(true);
    try {
      await apiClient.put('/api/v1/auth/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
      });
      setPasswordMessage({ type: 'success', text: 'Mot de passe modifié avec succès !' });
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      console.error('Password change error:', err);
      setPasswordMessage({ type: 'error', text: err.response?.data?.detail || 'Erreur lors du changement de mot de passe.' });
    } finally {
      setUpdatingPassword(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-slide-up">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-2xl font-bold text-white shadow-glow-sm">
            {avatars[avatarIndex]}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">
              <span>{t('profile.title', 'Mon Profil')}</span>
              <Badge variant="violet">{t('nav.student_portal', 'Étudiant')}</Badge>
            </h1>
            <p className="text-white/40 text-sm">{user?.email}</p>
          </div>
        </div>
        <p className="text-white/40 text-sm">
          {t('profile.subtitle', 'Gérez vos informations personnelles et identifiants de compte')}
        </p>
      </div>

      <div className="space-y-8">
        {/* Account Details & Profile Icon */}
        <form onSubmit={handleAccountSubmit}>
          <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
            <h3 className="form-section-title text-violet-400">{t('profile.title', 'Mon Profil')}</h3>
            
            {/* Profile Avatar Selector */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-white/70 mb-2">
                {t('profile.avatar', 'Avatar')}
              </label>
              <div className="flex flex-wrap gap-2.5">
                {avatars.map((av, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setAvatarIndex(idx)}
                    className={`w-11 h-11 rounded-xl text-lg font-bold transition-all border flex items-center justify-center ${
                      avatarIndex === idx
                        ? 'bg-violet-600 border-violet-500 text-white shadow-glow-sm scale-110'
                        : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    {av}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <Input
                label={t('profile.full_name', 'Nom complet')}
                type="text"
                name="name"
                value={accountData.name}
                onChange={(e) => setAccountData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
              <Input
                label={t('profile.email', 'Adresse email')}
                type="email"
                name="email"
                value={accountData.email}
                onChange={(e) => setAccountData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>

            {accountMessage && (
              <div className={`mt-4 rounded-xl p-4 flex items-center gap-3 border shadow-lg ${
                accountMessage.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                  : 'bg-red-500/10 border-red-500/20 text-red-300'
              }`}>
                <p className="text-sm font-semibold">{accountMessage.text}</p>
              </div>
            )}

            <div className="flex justify-end mt-6">
              <Button type="submit" variant="primary" loading={updatingAccount} disabled={updatingAccount}>
                {t('action.save', 'Enregistrer')}
              </Button>
            </div>
          </Card>
        </form>

        {/* Change Password */}
        <form onSubmit={handlePasswordSubmit}>
          <Card className="p-6 border border-white/10 bg-white/[0.03] backdrop-blur-md">
            <h3 className="form-section-title text-violet-400">{t('profile.change_password', 'Changer de mot de passe')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
              <Input
                label={t('profile.current_password', 'Mot de passe actuel')}
                type="password"
                name="currentPassword"
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                required
              />
              <Input
                label={t('profile.new_password', 'Nouveau mot de passe')}
                type="password"
                name="newPassword"
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                error={passwordErrors.newPassword}
                required
              />
              <Input
                label={t('profile.confirm_password', 'Confirmer le mot de passe')}
                type="password"
                name="confirmPassword"
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                error={passwordErrors.confirmPassword}
                required
              />
            </div>

            {passwordMessage && (
              <div className={`mt-4 rounded-xl p-4 flex items-center gap-3 border shadow-lg ${
                passwordMessage.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                  : 'bg-red-500/10 border-red-500/20 text-red-300'
              }`}>
                <p className="text-sm font-semibold">{passwordMessage.text}</p>
              </div>
            )}

            <div className="flex justify-end mt-6">
              <Button type="submit" variant="primary" loading={updatingPassword} disabled={updatingPassword}>
                {t('profile.update_password_btn', 'Mettre à jour le mot de passe')}
              </Button>
            </div>
          </Card>
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
