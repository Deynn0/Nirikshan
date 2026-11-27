import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Building2,
  FilePlus,
  Files,
  LogOut,
  Moon,
  Sun,
  ShieldCheck,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { LanguageToggle } from '../../i18n/LanguageToggle';

interface InstitutionPortalLayoutProps {
  children: React.ReactNode;
}

export const InstitutionPortalLayout: React.FC<InstitutionPortalLayoutProps> = ({ children }) => {
  const { session, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const username = session?.username || 'inst1';
  const displayName = session?.displayName || username;

  const isMyApps = location.pathname === '/portal';
  const isNewApp = location.pathname === '/portal/new';

  return (
    <div className="min-h-screen bg-[#FBF9F5] dark:bg-slate-950 text-stone-900 dark:text-slate-100 flex flex-col font-sans selection:bg-purple-200 selection:text-purple-900">
      {/* 1. Clean, Wide Dedicated Topbar (No Left Sidebar) */}
      <header className="sticky top-0 z-30 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-stone-200 dark:border-slate-800 px-4 sm:px-8 flex items-center justify-between shadow-2xs">
        {/* Brand & Portal Label */}
        <div className="flex items-center gap-6">
          <Link to="/portal" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Building2 className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-base text-stone-900 dark:text-white leading-tight flex items-center gap-1.5">
                Nirikshan
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 uppercase tracking-wider">
                  Portal
                </span>
              </span>
              <span className="text-[10px] text-sky-700 dark:text-sky-400 font-sans">
                निरीक्षण आवेदक संस्थान पोर्टल
              </span>
            </div>
          </Link>

          {/* Navigation Items (Topbar Only) */}
          <nav className="hidden md:flex items-center gap-1 ml-4 border-l border-stone-200 dark:border-slate-800 pl-4 text-xs font-semibold">
            <Link
              to="/portal"
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all ${
                isMyApps
                  ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 shadow-2xs'
                  : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-slate-800'
              }`}
            >
              <Files className="w-4 h-4" />
              <span>{t('My Applications') || 'My Applications'}</span>
            </Link>

            <Link
              to="/portal/new"
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all ${
                isNewApp
                  ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 shadow-2xs'
                  : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-slate-800'
              }`}
            >
              <FilePlus className="w-4 h-4" />
              <span>{t('New Application') || 'New Application'}</span>
            </Link>
          </nav>
        </div>

        {/* Right Topbar Elements: Bilingual Toggle, Theme Toggle, Institution Chip */}
        <div className="flex items-center gap-3">
          {/* Prominent Bilingual Support Toggle */}
          <div className="bg-stone-100 dark:bg-slate-800/80 p-0.5 rounded-full border border-stone-200 dark:border-slate-700 shadow-2xs flex items-center">
            <LanguageToggle />
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Institution User Chip & Logout */}
          <div className="flex items-center gap-2.5 pl-3 border-l border-stone-200 dark:border-slate-800">
            <div className="w-8 h-8 rounded-full bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 flex items-center justify-center font-bold text-xs ring-2 ring-sky-200 dark:ring-sky-800">
              {username.toUpperCase().slice(0, 4)}
            </div>
            <div className="hidden lg:flex flex-col text-left max-w-[200px]">
              <span className="text-xs font-bold text-stone-900 dark:text-white leading-tight truncate">
                {displayName}
              </span>
              <span className="text-[10px] text-stone-500 font-medium leading-tight capitalize">
                Applicant Institution ({username})
              </span>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-2 rounded-xl text-stone-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* 2. Wide Main Content Canvas */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 py-8">{children}</main>

      {/* 3. Footer */}
      <footer className="border-t border-stone-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/40 py-5 px-6 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-stone-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>AICTE Approval Process Handbook (APH) 2026–2027 Filing Portal</span>
          </div>
          <span className="text-stone-400 text-[11px]">
            Strict Air-Gap & Cryptographic Proof Verification Enabled
          </span>
        </div>
      </footer>
    </div>
  );
};
