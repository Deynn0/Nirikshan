import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, ShieldAlert, Globe, LogOut, UserCheck, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { session, role, logout, switchRole } = useAuth();
  const navigate = useNavigate();

  const toggleLanguage = () => {
    const nextLang = i18n.language.startsWith('hi') ? 'en' : 'hi';
    i18n.changeLanguage(nextLang);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-purple-600 p-0.5 shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Shield className="w-5 h-5 text-sky-400 group-hover:text-sky-300 transition-colors" />
              </div>
            </div>
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-xl font-black tracking-tight text-white font-sans">
                  Nirikshan
                </span>
                <span className="text-sm font-semibold text-sky-400">
                  (निरीक्षण)
                </span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wider uppercase font-mono">
                AICTE Regulatory Scrutiny
              </p>
            </div>
          </Link>

          {/* Airgap Security Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-[11px] font-mono text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Strict Air-Gap Local
          </div>
        </div>

        {/* Right Action Bar */}
        <div className="flex items-center gap-3">
          {/* Navigation Links for Role */}
          {session && (
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs font-medium">
              <button
                type="button"
                onClick={() => {
                  switchRole('applicant');
                  navigate('/applicant');
                }}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  role === 'applicant'
                    ? 'bg-sky-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t('nav.applicant')}
              </button>
              <button
                type="button"
                onClick={() => {
                  switchRole('officer');
                  navigate('/officer');
                }}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  role === 'officer'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t('nav.officer')}
              </button>
            </div>
          )}

          {/* Language Toggle */}
          <button
            type="button"
            onClick={toggleLanguage}
            title="Toggle English / हिंदी"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 text-xs text-slate-300 hover:bg-slate-800 transition-colors"
          >
            <Globe className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-semibold">{i18n.language.startsWith('hi') ? 'हिंदी' : 'English'}</span>
          </button>

          {/* User & Logout */}
          {session ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="hidden sm:block text-right">
                <div className="text-xs font-semibold text-slate-200 max-w-[120px] truncate">
                  {session.username}
                </div>
                <div className="text-[10px] text-sky-400 font-mono capitalize">
                  {session.role}
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                title={t('nav.logout')}
                className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
