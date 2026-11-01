import React, { useState } from 'react';
import { X, HelpCircle, ArrowRight, ExternalLink, ShieldAlert, Sparkles, Send } from 'lucide-react';
import { mockAskWhyDialogues } from '../../data/mockScrutinyData';
import { PillBadge } from '../common/PillBadge';

interface AskWhyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToDocument?: (docName: string, page: number) => void;
}

export const AskWhyDrawer: React.FC<AskWhyDrawerProps> = ({
  isOpen,
  onClose,
  onNavigateToDocument,
}) => {
  const [selectedDialogue, setSelectedDialogue] = useState(mockAskWhyDialogues[0]);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [customInput, setCustomInput] = useState('');

  if (!isOpen) return null;

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;

    // Simulate custom answer generation
    const newDialogue = {
      id: `custom-${Date.now()}`,
      question: customInput,
      answerSentences: [
        {
          text: `Analysis indicates statutory review factors for "${customInput}" depend on physical verification of cadastral boundaries.`,
          citationId: 'C-NEW-1',
          citationTitle: 'Revenue Survey Plot Map 42/1A',
        },
        {
          text: 'AICTE Clause 4.1.2 mandates registered lease continuity without encumbrances or third-party mortgages.',
          citationId: 'C-NEW-2',
          citationTitle: 'Sub-Registrar Encumbrance Certificate #2026/89',
          isWarning: true,
        },
      ],
    };
    setSelectedDialogue(newDialogue);
    setCustomInput('');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-stone-900/40 dark:bg-black/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
      />

      {/* Right Drawer Panel */}
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white dark:bg-slate-900 shadow-2xl border-l border-stone-200 dark:border-slate-800 flex flex-col justify-between animate-in slide-in-from-right duration-250">
          {/* Header */}
          <div className="px-6 py-5 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between bg-stone-50/70 dark:bg-slate-900/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/40 text-[#6D28D9] dark:text-purple-300 flex items-center justify-center">
                <HelpCircle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-base text-stone-900 dark:text-slate-100 flex items-center gap-2">
                  Ask Why Scrutiny Explainer
                  <PillBadge variant="violet" size="sm">
                    Interactive
                  </PillBadge>
                </h3>
                <p className="text-xs text-stone-500">
                  Every sentence is backed by sovereign records & cryptographic hashes
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Quick Question Chips */}
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-2">
                Frequently Asked Scrutiny Queries
              </span>
              <div className="space-y-1.5">
                {mockAskWhyDialogues.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      setSelectedDialogue(d);
                      setActiveCitation(null);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-between border ${
                      selectedDialogue.id === d.id
                        ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-300 dark:border-purple-700 text-purple-900 dark:text-purple-200 shadow-xs'
                        : 'bg-stone-50 dark:bg-slate-800/40 border-stone-200 dark:border-slate-800 text-stone-700 dark:text-slate-300 hover:border-stone-300'
                    }`}
                  >
                    <span className="line-clamp-1">{d.question}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-stone-400 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>

            {/* Active Dialogue Question & Sentence-by-Sentence Evidence */}
            <div className="surface-card bg-stone-50/50 dark:bg-slate-800/30 border border-stone-200 dark:border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-stone-900 dark:text-white pb-2 border-b border-stone-200 dark:border-slate-800">
                <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
                <span>{selectedDialogue.question}</span>
              </div>

              {/* Every Sentence Linked to Evidence */}
              <div className="space-y-3 pt-1">
                {selectedDialogue.answerSentences.map((s, idx) => {
                  const isHighlighted = activeCitation === s.citationId;
                  return (
                    <div
                      key={idx}
                      onMouseEnter={() => setActiveCitation(s.citationId)}
                      onClick={() => setActiveCitation(s.citationId)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer ${
                        isHighlighted
                          ? 'bg-purple-50 dark:bg-purple-950/50 border-purple-400 dark:border-purple-600 shadow-sm'
                          : s.isCritical
                          ? 'bg-rose-50/40 dark:bg-rose-950/20 border-rose-200/80 dark:border-rose-900/40'
                          : s.isWarning
                          ? 'bg-amber-50/40 dark:bg-amber-950/20 border-amber-200/80 dark:border-amber-900/40'
                          : 'bg-white dark:bg-slate-900 border-stone-200 dark:border-slate-800'
                      }`}
                    >
                      <p className="text-xs sm:text-sm text-stone-800 dark:text-slate-200 leading-relaxed font-sans">
                        {s.text}
                      </p>

                      <div className="mt-2.5 flex items-center justify-between text-[11px] pt-2 border-t border-stone-100 dark:border-slate-800">
                        <span className="inline-flex items-center gap-1 font-mono text-purple-700 dark:text-purple-300 font-semibold">
                          <ExternalLink className="w-3 h-3" />
                          Evidence: {s.citationTitle}
                        </span>
                        <PillBadge
                          variant={
                            s.isCritical ? 'critical' : s.isWarning ? 'warning' : 'verified'
                          }
                          size="sm"
                        >
                          {s.citationId}
                        </PillBadge>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Citation Inspector Detail */}
            {activeCitation && (
              <div className="p-4 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 text-xs animate-in fade-in duration-150">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-purple-950 dark:text-purple-200">
                    Active Sovereign Evidence Reference
                  </span>
                  <span className="font-mono text-[10px] text-purple-700 dark:text-purple-400">
                    {activeCitation}
                  </span>
                </div>
                <p className="text-stone-600 dark:text-slate-400 text-[11px]">
                  Directly verified from AICTE National Portal API & Maharashtra Sub-Registrar
                  Cadastral Ledger.
                </p>
                <div className="mt-2 text-[10px] font-mono text-stone-500 break-all bg-white dark:bg-slate-900 p-2 rounded border border-purple-100 dark:border-purple-900">
                  SHA-256: 4d83e2f1839a829104ebc7612c77d9401bf5199859f14ba6
                </div>
              </div>
            )}
          </div>

          {/* Drawer Footer Question Input */}
          <div className="p-4 border-t border-stone-200 dark:border-slate-800 bg-stone-50/80 dark:bg-slate-950">
            <form onSubmit={handleCustomSubmit} className="flex gap-2">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Ask about land norms, faculty ratios, or FDR lien..."
                className="flex-1 bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-stone-900 dark:text-white placeholder:text-stone-400 outline-none focus:border-purple-500"
              />
              <button
                type="submit"
                className="px-3.5 py-2 rounded-xl bg-[#6D28D9] hover:bg-[#5B21B6] text-white text-xs font-semibold flex items-center justify-center shrink-0 shadow-sm"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
            <p className="text-[10px] text-stone-400 text-center mt-2">
              Answers are synthesized deterministically from ingested evidence packs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
