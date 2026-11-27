import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Inbox,
  FileSearch,
  Network,
  Cpu,
  BookOpen,
  History,
  Server,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Sun,
  Moon,
  ChevronRight,
  User,
  Home,
  LogOut,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { CommandPaletteModal } from './CommandPaletteModal';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { session, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const currentRole =
    session?.appRole ||
    (session?.role === 'applicant' ? 'institution' : session?.role) ||
    'officer';
  const isVerifier = currentRole === 'verifier';

  // Derive initials from username
  const initials = session?.username
    ? session.username.slice(0, 2).toUpperCase()
    : 'U?';

  const pathname = location.pathname;

  // Active path checking (supporting both direct routes and /workspace aliases)
  const isReviewQueue =
    pathname === '/dashboard' ||
    pathname === '/workspace' ||
    pathname === '/workspace/queue' ||
    pathname.startsWith('/dashboard/application') ||
    pathname.startsWith('/workspace/application');
  const isAnalyse = pathname === '/analyse' || pathname === '/workspace/tools/analyse';
  const isIntegrity = pathname === '/integrity' || pathname === '/workspace/tools/integrity';
  const isIssuerSim = pathname === '/issuers' || pathname === '/workspace/tools/issuer-simulator';
  const isRules = pathname === '/rules' || pathname === '/workspace/governance/rules';
  const isAudit = pathname === '/audit' || pathname === '/workspace/governance/audit';
  const isPlatform = pathname === '/platform' || pathname === '/workspace/governance/platform';

  // Dynamic Breadcrumb generation
  let currentTitle = 'Review queue';
  if (pathname.includes('/application/')) {
    currentTitle = 'Application Details';
  } else if (isAnalyse) {
    currentTitle = 'Document Forensics & Analysis';
  } else if (isIntegrity) {
    currentTitle = 'Cross-College Integrity Graph';
  } else if (isIssuerSim) {
    currentTitle = 'Issuer Registry Simulator';
  } else if (isRules) {
    currentTitle = 'Regulatory Rules Browser';
  } else if (isAudit) {
    currentTitle = 'Audit Log';
  } else if (isPlatform) {
    currentTitle = 'Platform Settings & Keys';
  }

  const handleSelectApp = (id: string) => {
    navigate(`/workspace/application/${id}`);
  };

  let roleLabel = 'AICTE Scrutiny Officer';
  if (currentRole === 'verifier') {
    roleLabel = 'Verification Cell';
  } else if (currentRole === 'admin') {
    roleLabel = 'Administrator / Auditor';
  } else if (currentRole === 'institution') {
    roleLabel = 'Applicant Institution';
  }

  return (
    <div className="min-h-screen bg-[#FAF8F4] dark:bg-slate-950 text-stone-900 dark:text-slate-100 flex font-sans selection:bg-purple-200 selection:text-purple-900">
      {/* 1. Left Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 bg-white dark:bg-slate-900 border-r border-stone-200 dark:border-slate-800 transition-all duration-300 flex flex-col justify-between ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Top: Brand Logo */}
        <div>
          <div className="h-16 px-5 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#6D28D9] to-indigo-500 text-white flex items-center justify-center shrink-0 shadow-sm">
                <ShieldCheck className="w-4 h-4" />
              </div>
              {!collapsed && (
                <div className="flex flex-col">
                  <span className="font-extrabold text-sm text-stone-900 dark:text-white leading-tight">
                    Nirikshan
                  </span>
                  <span className="text-[10px] text-purple-700 dark:text-purple-400 font-sans">
                    निरीक्षण Scrutiny
                  </span>
                </div>
              )}
            </Link>
          </div>

          {/* Navigation Groups */}
          <nav className="p-3 space-y-6 text-xs">
            {/* Group 1: Review queue (on its own at the top) */}
            <div>
              {!collapsed && (
                <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  Review
                </div>
              )}
              <Link
                to="/dashboard"
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                  isReviewQueue
                    ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                    : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                }`}
                title={collapsed ? 'Review queue' : undefined}
              >
                <Inbox className="w-4 h-4 shrink-0" />
                {!collapsed && <span>Review queue (/dashboard)</span>}
              </Link>
            </div>

            {/* Group 2: Tools (Analyse a document, Integrity, Issuer simulator) */}
            <div>
              {!collapsed && (
                <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  Tools
                </div>
              )}
              <div className="space-y-1">
                <Link
                  to="/analyse"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isAnalyse
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Document Forensics & Analysis' : undefined}
                >
                  <FileSearch className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Document Forensics (/analyse)</span>}
                </Link>

                <Link
                  to="/integrity"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isIntegrity
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Cross-College Integrity Graph' : undefined}
                >
                  <Network className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Integrity Graph (/integrity)</span>}
                </Link>

                <Link
                  to="/issuers"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isIssuerSim
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Issuer Registry Simulator' : undefined}
                >
                  <Cpu className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Issuer Simulator (/issuers)</span>}
                </Link>
              </div>
            </div>

            {/* Group 3: Governance (Rules, Audit log, Platform) */}
            <div>
              {!collapsed && (
                <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  Governance
                </div>
              )}
              <div className="space-y-1">
                <Link
                  to="/rules"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isRules
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Regulatory Rules Browser' : undefined}
                >
                  <BookOpen className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Regulatory Rules (/rules)</span>}
                </Link>

                {/* Audit Log and Platform are hidden from Verifiers */}
                {!isVerifier && (
                  <>
                    <Link
                      to="/audit"
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                        isAudit
                          ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                          : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                      }`}
                      title={collapsed ? 'Audit Log' : undefined}
                    >
                      <History className="w-4 h-4 shrink-0" />
                      {!collapsed && <span>Audit Log (/audit)</span>}
                    </Link>

                    <Link
                      to="/platform"
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                        isPlatform
                          ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                          : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                      }`}
                      title={collapsed ? 'Platform Settings & Keys' : undefined}
                    >
                      <Server className="w-4 h-4 shrink-0" />
                      {!collapsed && <span>Platform Settings (/platform)</span>}
                    </Link>
                  </>
                )}
              </div>
            </div>
          </nav>
        </div>

        {/* Bottom: Collapse Button */}
        <div className="p-3 border-t border-stone-200 dark:border-slate-800">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center gap-2 p-2.5 rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors text-xs font-medium"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <PanelLeftOpen className="w-4 h-4" />
            ) : (
              <>
                <PanelLeftClose className="w-4 h-4" />
                <span>Collapse sidebar</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* 2. Main Workspace Layout */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${
          collapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        {/* Top Bar with Breadcrumbs, Ctrl+K Search, Theme Toggle, User Chip */}
        <header className="sticky top-0 z-30 h-16 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-stone-200 dark:border-slate-800 px-6 flex items-center justify-between gap-4">
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-xs text-stone-500 overflow-hidden">
            <Link
              to="/dashboard"
              className="hover:text-purple-700 dark:hover:text-purple-400 transition-colors shrink-0"
            >
              Workspace
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-stone-400 shrink-0" />
            <Link
              to="/dashboard"
              className="hover:text-purple-700 dark:hover:text-purple-400 transition-colors shrink-0"
            >
              {currentTitle}
            </Link>
            {pathname.includes('/application/') && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                <span className="font-semibold text-stone-900 dark:text-white truncate">
                  Application Dossier
                </span>
              </>
            )}
          </div>

          {/* Right Header Items: Ctrl+K, Theme Toggle, User Chip */}
          <div className="flex items-center gap-3">
            {/* Ctrl+K Search Box */}
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 hover:border-purple-300 text-stone-500 text-xs transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Search dossiers...</span>
              <kbd className="px-1.5 py-0.5 text-[10px] font-mono text-stone-400 bg-white dark:bg-slate-900 rounded border border-stone-200 dark:border-slate-700 shadow-2xs">
                Ctrl+K
              </kbd>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-stone-500 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* User Chip: Name, Role and Logout */}
            <div className="flex items-center gap-2.5 pl-3 border-l border-stone-200 dark:border-slate-800">
              <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 flex items-center justify-center font-bold text-xs ring-2 ring-purple-200 dark:ring-purple-800">
                {initials}
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-xs font-bold text-stone-900 dark:text-white leading-tight">
                  {session?.username ?? 'Guest'}
                </span>
                <span className="text-[10px] text-stone-500 font-medium leading-tight">
                  {roleLabel}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-2 rounded-xl text-stone-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* Workspace Page Body */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {isVerifier && (isAudit || isPlatform) ? (
            <div className="rounded-2xl border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/30 p-8 text-center space-y-3">
              <h2 className="text-base font-bold text-rose-800 dark:text-rose-200">
                Access Restricted (Verification Cell)
              </h2>
              <p className="text-xs text-rose-700 dark:text-rose-300 max-w-md mx-auto">
                Verification cell operators are restricted from accessing governance audit chains and platform security keys.
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="mt-3 px-4 py-2 rounded-xl bg-purple-700 text-white text-xs font-semibold cursor-pointer"
              >
                Return to Review Queue
              </button>
            </div>
          ) : (
            children
          )}
        </main>

        {/* Footer Disclaimer */}
        <footer className="border-t border-stone-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/40 py-4 px-6">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-stone-500">
            <span className="font-mono">
              AICTE Directorate Scrutiny Console · Node: WRO-MUMBAI-04
            </span>
            <span className="font-medium text-stone-600 dark:text-slate-400 text-center">
              Decision support only. Findings are preliminary indicators for review.
            </span>
            <span>Security Level: E5 Cryptographic Notary</span>
          </div>
        </footer>
      </div>

      {/* Command Palette Modal */}
      <CommandPaletteModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectApplication={handleSelectApp}
      />
    </div>
  );
};
