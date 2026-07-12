import { useNavigate } from 'react-router-dom';
import { Result } from 'antd';
import { useLanguage } from '../context/LanguageContext';
import Button from '../components/ui/Button';

const NotFoundPage = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4 py-16">
      {/* Ambient glow orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-violet-600/20 blur-[100px] animate-pulse-slow" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-indigo-600/20 blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full bg-cyan-600/10 blur-[80px]" />
      </div>

      <div className="relative w-full max-w-lg animate-slide-up text-center">
        <div className="glass-strong rounded-3xl p-8 md:p-12 shadow-glass border border-white/10">
          <Result
            status="404"
            title={<h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-indigo-400">404</h1>}
            subTitle={
              <div className="space-y-2 mt-4">
                <h2 className="text-xl font-semibold text-white">{t('error.404.title')}</h2>
                <p className="text-sm text-white/50">{t('error.404.subtitle')}</p>
              </div>
            }
            extra={
              <div className="mt-8 flex justify-center">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => navigate('/')}
                >
                  {t('error.back_home')}
                </Button>
              </div>
            }
          />
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
