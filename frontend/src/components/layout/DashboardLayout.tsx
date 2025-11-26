import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../services/authStore';
import { useAuth } from '../../hooks/useAuth';
import { Brain, LayoutDashboard, Globe, LogOut, User } from 'lucide-react';
import clsx from 'clsx';

interface SidebarItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ to, icon, label, active }) => (
  <Link
    to={to}
    className={clsx(
      'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
      active
        ? 'bg-brand-500/10 text-brand-400'
        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
    )}
  >
    {icon}
    <span className="font-medium">{label}</span>
  </Link>
);

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col fixed h-full z-10">
        <div className="p-6 border-b border-slate-800">
          <Link to="/" className="flex items-center gap-2 text-brand-400">
            <Brain className="w-8 h-8" />
            <span className="text-xl font-display font-bold text-white">Idea Inc</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <SidebarItem 
            to="/dashboard" 
            icon={<LayoutDashboard className="w-5 h-5" />} 
            label="Dashboard" 
            active={location.pathname === '/dashboard'}
          />
          <SidebarItem 
            to="/worlds" 
            icon={<Globe className="w-5 h-5" />} 
            label="Simulation Worlds" 
            active={location.pathname.startsWith('/worlds')}
          />
          {/* Add more nav items here */}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400">
              <User className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.display_name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Log Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

