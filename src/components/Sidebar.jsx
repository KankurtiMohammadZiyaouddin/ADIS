import { NavLink, useNavigate } from 'react-router-dom';
import { primaryNav, moduleNav, systemNav } from './navConfig';

function NavItem({ to, label, icon, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-150 ${
          isActive
            ? 'bg-primary-container text-on-primary-container font-bold'
            : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest'
        }`
      }
    >
      <span className="material-symbols-outlined">{icon}</span>
      <span className="text-label-md">{label}</span>
    </NavLink>
  );
}

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <nav className="hidden md:flex flex-col h-full py-padding-default shrink-0 bg-surface-container w-[260px] fixed left-0 top-0 border-r border-outline-variant z-20">
      <div className="px-6 pb-6 border-b border-outline-variant mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-on-primary font-black text-sm">
            A
          </div>
          <div>
            <h1 className="text-title-lg font-title-lg font-black text-primary tracking-tight">ADIS</h1>
            <p className="text-label-sm text-on-surface-variant">Forensic Suite</p>
          </div>
        </div>
        <button
          onClick={() => navigate('/cases')}
          className="mt-6 w-full bg-primary text-on-primary py-2 rounded text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm"
        >
          New Investigation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 space-y-1">
        {primaryNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        <div className="pt-4 pb-2 px-4 text-label-sm text-outline font-semibold uppercase tracking-wider">
          Modules
        </div>
        {moduleNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        <div className="pt-4 pb-2 px-4 text-label-sm text-outline font-semibold uppercase tracking-wider">
          System
        </div>
        {systemNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
      </div>

      <div className="mt-auto px-4 pt-4 border-t border-outline-variant">
        <NavLink
          to="/login"
          className="flex items-center gap-3 px-4 py-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-colors rounded-lg"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="text-label-md">Sign Out</span>
        </NavLink>
      </div>
    </nav>
  );
}

