import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, Building2, ShieldAlert, Cpu, ArrowRight, X } from 'lucide-react';
import { mockApplications, mockFindings } from '../../data/mockScrutinyData';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectApplication: (id: string) => void;
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  onSelectApplication,
}) => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        }
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredApps = mockApplications.filter(
    (app) =>
      app.name.toLowerCase().includes(query.toLowerCase()) ||
      app.id.toLowerCase().includes(query.toLowerCase()) ||
      app.location.toLowerCase().includes(query.toLowerCase())
  );

  const filteredFindings = mockFindings.filter(
    (f) =>
      f.title.toLowerCase().includes(query.toLowerCase()) ||
      f.ruleId.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-stone-900/40 dark:bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-floating border border-stone-200 dark:border-slate-800 overflow-hidden flex flex-col">
        {/* Search Input */}
        <div className="flex items-center px-4 py-3.5 border-b border-stone-200 dark:border-slate-800 gap-3">
          <Search className="w-5 h-5 text-purple-600 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search institutions, rules, findings, document hashes..."
            className="w-full bg-transparent text-sm text-stone-900 dark:text-slate-100 placeholder:text-stone-400 outline-none"
          />
          <kbd className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono text-stone-400 bg-stone-100 dark:bg-slate-800 rounded border border-stone-200 dark:border-slate-700">
            ESC
          </kbd>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-stone-400 hover:text-stone-600 dark:hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-3 space-y-4">
          {/* Applications Section */}
          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              Institutions & Applications ({filteredApps.length})
            </div>
            <div className="mt-1 space-y-1">
              {filteredApps.map((app) => (
                <button
                  key={app.id}
                  onClick={() => {
                    onSelectApplication(app.id);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-purple-50 dark:hover:bg-purple-950/30 text-left transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-stone-100 dark:bg-slate-800 text-stone-600 dark:text-slate-300 flex items-center justify-center group-hover:bg-purple-100 group-hover:text-purple-700 transition-colors">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-stone-900 dark:text-slate-100">
                        {app.name}
                      </p>
                      <p className="text-[11px] text-stone-500 font-mono">
                        {app.id} · {app.location}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-stone-400">Risk: {app.riskScore}/100</span>
                    <ArrowRight className="w-3.5 h-3.5 text-stone-400 group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Findings & Rules Section */}
          {filteredFindings.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-stone-400">
                Statutory Rules & Findings ({filteredFindings.length})
              </div>
              <div className="mt-1 space-y-1">
                {filteredFindings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => {
                      onSelectApplication('APP-2026-AICTE-4891');
                      onClose();
                    }}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-stone-50 dark:hover:bg-slate-800 text-left transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 flex items-center justify-center">
                        <ShieldAlert className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-xs font-medium text-stone-900 dark:text-slate-100 line-clamp-1">
                          {f.title}
                        </p>
                        <p className="text-[10px] font-mono text-stone-500">
                          {f.ruleId} · {f.documentRef}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] uppercase font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full">
                      {f.severityLabel}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="px-4 py-2.5 bg-stone-50 dark:bg-slate-950 border-t border-stone-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-400">
          <span>Tip: Press ↵ to view dossier or ESC to close</span>
          <span className="font-mono">AICTE Scrutiny v2.4</span>
        </div>
      </div>
    </div>
  );
};
