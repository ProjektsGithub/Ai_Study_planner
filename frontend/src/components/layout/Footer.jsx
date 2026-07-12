import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="mt-auto border-t border-white/[0.06] bg-white/[0.02]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center">
              <span className="text-xs">✦</span>
            </div>
            <span className="text-sm text-white/30 font-medium">
              © 2026 <span className="gradient-text font-semibold">AI Study Planner</span>
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6">
            {['À propos', 'Documentation', 'Support'].map((item) => (
              <a
                key={item}
                href="#"
                className="text-xs text-white/30 hover:text-white/70 transition-colors duration-200"
              >
                {item}
              </a>
            ))}
          </div>

          {/* Status */}
          <div className="flex items-center gap-2 text-xs text-white/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Tous les services opérationnels
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
