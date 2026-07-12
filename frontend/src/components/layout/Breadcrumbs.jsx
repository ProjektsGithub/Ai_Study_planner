import { Link, useLocation } from 'react-router-dom';

const routeNames = {
  dashboard: 'Dashboard',
  progression: 'Progression Académique',
  subjects: 'Matières',
  exams: 'Examens',
  'ai-plan': 'Planning IA',
  recommendations: 'Recommandations IA',
  profile: 'Profil',
  availabilities: 'Disponibilités',
  constraints: 'Contraintes',
  planner: 'Planificateur',
};

const Breadcrumbs = () => {
  const { pathname } = useLocation();
  const pathnames = pathname.split('/').filter((x) => x);

  if (pathnames.length === 0) return null;

  return (
    <nav className="flex items-center gap-2 text-xs text-white/40 mb-6 select-none animate-fade-in">
      <Link to="/dashboard" className="hover:text-white transition-colors flex items-center gap-1">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        Accueil
      </Link>
      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const name = routeNames[value] || value.charAt(0).toUpperCase() + value.slice(1);

        return (
          <div key={to} className="flex items-center gap-2">
            <span className="text-white/20">/</span>
            {isLast ? (
              <span className="text-white/80 font-medium truncate max-w-[150px]">{name}</span>
            ) : (
              <Link to={to} className="hover:text-white transition-colors truncate max-w-[150px]">
                {name}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
};

export default Breadcrumbs;
