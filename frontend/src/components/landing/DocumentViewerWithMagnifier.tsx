import React, { useState, useRef } from 'react';
import { PillBadge } from '../common/PillBadge';
import { ShieldCheck, AlertCircle, FileCheck2, Search, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

interface Revision {
  id: number;
  label: string;
  type: 'signed' | 'form' | 'edited';
  date: string;
  author: string;
  badgeText: string;
  summary: string;
}

const revisions: Revision[] = [
  {
    id: 1,
    label: 'Revision 1 · Signed',
    type: 'signed',
    date: '2026-03-12 11:20 AM',
    author: 'Principal Dr. A. Kothari',
    badgeText: 'Signed',
    summary: 'Initial digital submission. Cryptographic PKCS#7 signature valid with SHA-256 seal.',
  },
  {
    id: 2,
    label: 'Revision 2 · Form Changes',
    type: 'form',
    date: '2026-03-18 03:45 PM',
    author: 'Registrar Staff',
    badgeText: 'Form changes',
    summary: 'Updated sanctioned intake spreadsheet table and updated laboratory terminal roster.',
  },
  {
    id: 3,
    label: 'Revision 3 · Post-Sign Alteration',
    type: 'edited',
    date: '2026-03-24 09:12 AM',
    author: 'Unknown Origin / Appended Stream',
    badgeText: 'Edits after signing',
    summary: 'WARNING: Incremental PDF stream altered carpet area figure (8,450 -> 12,450 sqm).',
  },
];

export const DocumentViewerWithMagnifier: React.FC = () => {
  const [activeRev, setActiveRev] = useState<number>(1);
  const [lensPos, setLensPos] = useState<{ x: number; y: number } | null>(null);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setLensPos({ x, y });
  };

  const currentRevision = revisions.find((r) => r.id === activeRev) || revisions[0];

  return (
    <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl shadow-soft overflow-hidden">
      {/* Viewer Header */}
      <div className="px-6 py-4 border-b border-stone-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-stone-50/70 dark:bg-slate-900/80">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center text-purple-700 dark:text-purple-300">
            <FileCheck2 className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-stone-900 dark:text-slate-100 text-sm">
                Architect_Builtup_Area_Certificate.pdf
              </h4>
              <PillBadge variant="verified" size="sm">
                Revision 1 · Signed
              </PillBadge>
            </div>
            <p className="text-xs text-stone-500 font-mono">
              SHA-256: 4d83e2f1839a829104ebc7612c77d9401bf5199859f14ba6 · Page 12 of 18
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-stone-500">
          <span className="flex items-center gap-1 bg-white dark:bg-slate-800 px-2.5 py-1 rounded-md border border-stone-200 dark:border-slate-700">
            <Search className="w-3.5 h-3.5 text-purple-600" />
            Hover to magnify forensic layer
          </span>
        </div>
      </div>

      {/* Main Grid: Document Viewer on Left, Revision List on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Document Viewer (Left 8 cols) */}
        <div className="lg:col-span-8 p-6 bg-stone-100/60 dark:bg-slate-950/50 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-stone-200 dark:border-slate-800">
          <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="relative w-full max-w-xl aspect-[1/1.3] bg-white dark:bg-slate-900 rounded-lg shadow-md border border-stone-300 dark:border-slate-700 p-8 select-none cursor-crosshair overflow-hidden transition-shadow hover:shadow-xl"
          >
            {/* Document Content Simulation */}
            <div className="space-y-4 text-stone-800 dark:text-slate-200 text-xs leading-relaxed font-sans">
              <div className="border-b-2 border-stone-900 dark:border-slate-400 pb-3 flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-sm tracking-wide uppercase text-stone-900 dark:text-slate-100">
                    Council of Architecture Certified Survey
                  </h3>
                  <p className="text-[11px] text-stone-500">Form AICTE-APH-2026/Schedule-IV · Carpet Area Certificate</p>
                </div>
                <div className="w-12 h-12 rounded border border-stone-400 dark:border-slate-600 flex items-center justify-center text-[10px] text-center font-mono font-bold text-stone-500">
                  SEAL
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[11px] pt-1">
                <div>
                  <span className="text-stone-400 uppercase text-[9px] block">Institution</span>
                  <strong className="text-stone-900 dark:text-white">Apex Institute of Tech & Mgmt</strong>
                </div>
                <div>
                  <span className="text-stone-400 uppercase text-[9px] block">Survey Plot Cadastre</span>
                  <strong className="font-mono">Plot 42/1A, Haveli, Pune</strong>
                </div>
              </div>

              {/* Table of measurements */}
              <div className="border border-stone-200 dark:border-slate-700 rounded overflow-hidden mt-3">
                <table className="w-full text-[11px] text-left">
                  <thead className="bg-stone-50 dark:bg-slate-800 text-stone-500 uppercase text-[9px]">
                    <tr>
                      <th className="p-2">Wing / Floor</th>
                      <th className="p-2">Declared (Sqm)</th>
                      <th className="p-2">Inspected (Sqm)</th>
                      <th className="p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
                    <tr>
                      <td className="p-2 font-medium">Instructional Block A</td>
                      <td className="p-2 font-mono">5,840.00</td>
                      <td className="p-2 font-mono">5,840.00</td>
                      <td className="p-2 text-emerald-600 font-semibold">Matched</td>
                    </tr>
                    <tr>
                      <td className="p-2 font-medium">Administrative Block</td>
                      <td className="p-2 font-mono">1,620.00</td>
                      <td className="p-2 font-mono">1,620.00</td>
                      <td className="p-2 text-emerald-600 font-semibold">Matched</td>
                    </tr>
                    <tr
                      className={
                        activeRev === 3
                          ? 'bg-rose-50 dark:bg-rose-950/40 border-l-4 border-rose-500 font-bold'
                          : ''
                      }
                    >
                      <td className="p-2">
                        Laboratory Wing C
                        {activeRev === 3 && (
                          <span className="block text-[10px] text-rose-600 font-semibold">
                            ⚠ Post-sign font glyph swap detected!
                          </span>
                        )}
                      </td>
                      <td className="p-2 font-mono">
                        {activeRev === 3 ? (
                          <span className="line-through text-stone-400 mr-1">8,450</span>
                        ) : null}
                        <span className={activeRev === 3 ? 'text-rose-600 font-bold' : ''}>
                          {activeRev === 3 ? '12,450.00' : '8,450.00'}
                        </span>
                      </td>
                      <td className="p-2 font-mono">8,450.00</td>
                      <td className="p-2">
                        {activeRev === 3 ? (
                          <span className="text-rose-600 font-bold">Contradicted</span>
                        ) : (
                          <span className="text-emerald-600 font-semibold">Matched</span>
                        )}
                      </td>
                    </tr>
                    <tr className="bg-stone-50 dark:bg-slate-800/60 font-semibold">
                      <td className="p-2">Total Carpet Area</td>
                      <td className="p-2 font-mono text-purple-700 dark:text-purple-400">
                        {activeRev === 3 ? '19,910.00 sqm' : '15,910.00 sqm'}
                      </td>
                      <td className="p-2 font-mono">15,910.00 sqm</td>
                      <td className="p-2">
                        {activeRev === 3 ? (
                          <span className="text-rose-600 font-bold">Deficient</span>
                        ) : (
                          <span className="text-emerald-600 font-semibold">Verified</span>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Digital Signature stamp box */}
              <div
                className={`p-3 rounded-lg border text-[11px] mt-4 flex items-center justify-between ${
                  activeRev === 3
                    ? 'border-rose-300 bg-rose-50/70 text-rose-900'
                    : 'border-emerald-300 bg-emerald-50/70 text-emerald-900'
                }`}
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck
                    className={`w-5 h-5 ${activeRev === 3 ? 'text-rose-600' : 'text-emerald-600'}`}
                  />
                  <div>
                    <p className="font-semibold text-xs">
                      {activeRev === 3
                        ? 'Digital Signature Broken / Integrity Invalid'
                        : 'Digitally Signed by Architect R. K. Joshi (CA/2009/4819)'}
                    </p>
                    <p className="font-mono text-[10px] text-stone-500">
                      Timestamp: 2026-03-12 11:18:24 UTC · Certificate Authority: eMudhra Sub-CA 2025
                    </p>
                  </div>
                </div>
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                    activeRev === 3 ? 'bg-rose-200 text-rose-800' : 'bg-emerald-200 text-emerald-800'
                  }`}
                >
                  {activeRev === 3 ? 'Tampered' : 'Valid'}
                </span>
              </div>
            </div>

            {/* Magnifier Lens Element */}
            {isHovered && lensPos && (
              <div
                style={{
                  left: lensPos.x - 70,
                  top: lensPos.y - 70,
                  width: 140,
                  height: 140,
                }}
                className="pointer-events-none absolute rounded-full border-2 border-purple-600 dark:border-purple-400 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden z-20 ring-4 ring-purple-500/20"
              >
                {/* Magnified simulation target */}
                <div
                  style={{
                    transform: `translate(${-lensPos.x * 2.2 + 70}px, ${-lensPos.y * 2.2 + 70}px) scale(2.2)`,
                    transformOrigin: '0 0',
                    width: containerRef.current?.offsetWidth || 500,
                  }}
                  className="p-8 text-stone-800 dark:text-slate-100 text-xs select-none"
                >
                  <div className="border-b border-stone-800 pb-2">
                    <h3 className="font-bold text-xs uppercase">Council of Architecture Certified Survey</h3>
                    <p className="text-[10px] text-stone-500">Form AICTE-APH-2026/Schedule-IV</p>
                  </div>
                  <div className="mt-3 text-[10px]">
                    <p>Laboratory Wing C Area:</p>
                    <p className="font-mono font-bold text-purple-700 dark:text-purple-300">
                      {activeRev === 3 ? '12,450.00 sqm [OVERWRITTEN]' : '8,450.00 sqm [ORIGINAL]'}
                    </p>
                    <p className="text-[9px] text-stone-400 font-mono mt-1">
                      Glyph Offset: 0x004F8A20 · Font: ArialMT
                    </p>
                  </div>
                </div>
                {/* Crosshair indicator */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-2.5 h-2.5 rounded-full border border-purple-600 bg-purple-400/30" />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Revision List on Right (Right 4 cols) */}
        <div className="lg:col-span-4 p-6 bg-white dark:bg-slate-900 flex flex-col justify-between">
          <div>
            <div className="mb-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 dark:text-stone-500">
                Audit Revision History
              </span>
              <h5 className="text-base font-bold text-stone-900 dark:text-slate-100">
                Document Version Timeline
              </h5>
              <p className="text-xs text-stone-500 mt-1">
                Color-coded by regulatory trust integrity: Green for signed, Blue for form changes, Red for edits after signing.
              </p>
            </div>

            <div className="space-y-3">
              {revisions.map((rev) => {
                const isSelected = activeRev === rev.id;
                let badgeVariant: 'verified' | 'blue' | 'critical' = 'verified';
                let borderAccent = 'hover:border-emerald-300';
                let indicatorColor = 'bg-emerald-500';

                if (rev.type === 'form') {
                  badgeVariant = 'blue';
                  borderAccent = 'hover:border-sky-300';
                  indicatorColor = 'bg-sky-500';
                } else if (rev.type === 'edited') {
                  badgeVariant = 'critical';
                  borderAccent = 'hover:border-rose-300';
                  indicatorColor = 'bg-rose-500';
                }

                return (
                  <button
                    key={rev.id}
                    onClick={() => setActiveRev(rev.id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all relative ${
                      isSelected
                        ? 'bg-purple-50/50 dark:bg-purple-950/20 border-purple-300 dark:border-purple-700 shadow-sm ring-1 ring-purple-400/40'
                        : `bg-stone-50/50 dark:bg-slate-800/40 border-stone-200 dark:border-slate-800 ${borderAccent}`
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${indicatorColor}`} />
                        <span className="font-semibold text-xs text-stone-900 dark:text-slate-100">
                          {rev.label}
                        </span>
                      </div>
                      <PillBadge variant={badgeVariant} size="sm">
                        {rev.badgeText}
                      </PillBadge>
                    </div>

                    <p className="text-[11px] text-stone-600 dark:text-slate-400 line-clamp-2 mt-1">
                      {rev.summary}
                    </p>

                    <div className="mt-2 flex items-center justify-between text-[10px] text-stone-400 font-mono">
                      <span>{rev.author}</span>
                      <span>{rev.date}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active summary box */}
          <div className="mt-6 pt-4 border-t border-stone-200 dark:border-slate-800">
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-stone-50 dark:bg-slate-800/60 border border-stone-200 dark:border-slate-700 text-xs">
              <AlertCircle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-stone-900 dark:text-slate-200">
                  {currentRevision.type === 'edited'
                    ? 'Forensic Warning on Revision 3'
                    : 'Statutory Verification Status'}
                </p>
                <p className="text-stone-500 text-[11px] mt-0.5">{currentRevision.summary}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
