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
import { CommandPaletteModal } from './CommandPaletteModal';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const pathname = location.pathname;

  // Active path checking
  const isReviewQueue =
    pathname === '/workspace' ||
    pathname === '/workspace/queue' ||
    pathname.startsWith('/workspace/application');
  const isAnalyse = pathname === '/workspace/tools/analyse';
  const isIntegrity = pathname === '/workspace/tools/integrity';
  const isIssuerSim = pathname === '/workspace/tools/issuer-simulator';
  const isRules = pathname === '/workspace/governance/rules';
  const isAudit = pathname === '/workspace/governance/audit';
  const isPlatform = pathname === '/workspace/governance/platform';

  // Dynamic Breadcrumb generation
  let currentTitle = 'Review queue';
  if (pathname.includes('/application/')) {
    currentTitle = 'Apex Institute of Technology & Management';
  } else if (isAnalyse) {
    currentTitle = 'Analyse a document';
  } else if (isIntegrity) {
    currentTitle = 'Integrity network';
  } else if (isIssuerSim) {
    currentTitle = 'Issuer simulator';
  } else if (isRules) {
    currentTitle = 'Rules catalog';
  } else if (isAudit) {
    currentTitle = 'Audit log';
  } else if (isPlatform) {
    currentTitle = 'Platform health';
  }

  const handleSelectApp = (id: string) => {
    navigate(`/workspace/application/${id}`);
  };

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
                  Queue
                </div>
              )}
              <Link
                to="/workspace/queue"
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                  isReviewQueue
                    ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                    : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                }`}
                title={collapsed ? 'Review queue' : undefined}
              >
                <Inbox className="w-4 h-4 shrink-0" />
                {!collapsed && <span>Review queue</span>}
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
                  to="/workspace/tools/analyse"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isAnalyse
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Analyse a document' : undefined}
                >
                  <FileSearch className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Analyse a document</span>}
                </Link>

                <Link
                  to="/workspace/tools/integrity"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isIntegrity
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Integrity' : undefined}
                >
                  <Network className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Integrity</span>}
                </Link>

                <Link
                  to="/workspace/tools/issuer-simulator"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isIssuerSim
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Issuer simulator' : undefined}
                >
                  <Cpu className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Issuer simulator</span>}
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
                  to="/workspace/governance/rules"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isRules
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Rules' : undefined}
                >
                  <BookOpen className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Rules</span>}
                </Link>

                <Link
                  to="/workspace/governance/audit"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isAudit
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Audit log' : undefined}
                >
                  <History className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Audit log</span>}
                </Link>

                <Link
                  to="/workspace/governance/platform"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all ${
                    isPlatform
                      ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-xs border border-purple-200 dark:border-purple-800'
                      : 'text-stone-600 dark:text-slate-400 hover:bg-stone-50 dark:hover:bg-slate-800/60 hover:text-stone-900 dark:hover:text-white'
                  }`}
                  title={collapsed ? 'Platform' : undefined}
                >
                  <Server className="w-4 h-4 shrink-0" />
                  {!collapsed && <span>Platform</span>}
                </Link>
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
              to="/workspace"
              className="hover:text-purple-700 dark:hover:text-purple-400 transition-colors shrink-0"
            >
              Workspace
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-stone-400 shrink-0" />
            <Link
              to="/workspace/queue"
              className="hover:text-purple-700 dark:hover:text-purple-400 transition-colors shrink-0"
            >
              Review queue
            </Link>
            {pathname.includes('/application/') && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                <span className="font-semibold text-stone-900 dark:text-white truncate">
                  {currentTitle}
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

            {/* User Chip: Name and Role */}
            <div className="flex items-center gap-2.5 pl-3 border-l border-stone-200 dark:border-slate-800">
              <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 flex items-center justify-center font-bold text-xs ring-2 ring-purple-200 dark:ring-purple-800">
                SS
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-xs font-bold text-stone-900 dark:text-white leading-tight">
                  Dr. Sunita Sharma
                </span>
                <span className="text-[10px] text-stone-500 font-medium leading-tight">
                  Senior Scrutiny Officer
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Workspace Page Body */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>

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
