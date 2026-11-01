import React, { useState } from 'react';
import { History, Play, Pause, ChevronLeft, ChevronRight, GitCommit, FileDiff, CheckCircle2, ArrowRight } from 'lucide-react';

interface Revision {
  version: number;
  label: string;
  date: string;
  author: string;
  summary: string;
  sha256: string;
  addedText: string[];
  removedText: string[];
  paramDiffs: Array<{ field: string; oldVal: string; newVal: string; status: 'RESOLVED' | 'MODIFIED' }>;
  bodyContent: string;
}

const REVISIONS: Revision[] = [
  {
    version: 1,
    label: 'Rev 1.0 (Initial Filing)',
    date: '2026-08-12 11:20 AM',
    author: 'Registrar (Applicant)',
    summary: 'Initial dossier submission. Contained deficit in faculty cadre and expired Fire NOC.',
    sha256: 'a3f9e8...7b21',
    addedText: [
      'Original Land Deed submitted for Survey Plot 44/A measuring 4.80 Acres.',
      'Department of Computer Science: 0 Professors, 4 Associate Professors, 14 Asst Professors.',
      'Fire NOC Certificate No. FS-2023-998 expiring 30-June-2026.',
    ],
    removedText: [],
    paramDiffs: [
      { field: 'Land Area', oldVal: '—', newVal: '4.80 Acres', status: 'MODIFIED' },
      { field: 'Faculty Professors', oldVal: '—', newVal: '0 Professors', status: 'MODIFIED' },
      { field: 'Fire NOC Status', oldVal: '—', newVal: 'Expired', status: 'MODIFIED' },
    ],
    bodyContent: `SCHEDULE OF PROPERTY (REV 1):
Total land parcel measuring 4.80 Acres in Revenue Village Rampur.
Cadre Roster: Total 18 faculty members (0 Professors, 4 Associate, 14 Assistant).
Fire Safety: Inspection conducted under NOC FS-2023-998 (Valid until June 2026).`,
  },
  {
    version: 2,
    label: 'Rev 2.0 (Deficiency Rectification)',
    date: '2026-09-28 03:45 PM',
    author: 'Registrar (Applicant)',
    summary: 'Response to AICTE Deficiency Notice DEF-2026-089. Added supplementary land parcel and new Professor appointment.',
    sha256: 'b4c7d1...9e44',
    addedText: [
      '+ Supplementary registered lease deed for adjacent Plot 44/B adding 0.70 Acres (Total: 5.50 Acres).',
      '+ Appointment Order for Dr. S. Ramanujan (Ph.D.) as regular Professor in Computer Science.',
      '+ Fire Safety NOC Renewal Application acknowledgement slip from State Fire Directorate.',
    ],
    removedText: [
      '- Former land measurement 4.80 Acres superseded by unified contiguous survey of 5.50 Acres.',
      '- Former 0 Professor count updated to 1 Regular Professor.',
    ],
    paramDiffs: [
      { field: 'Land Area', oldVal: '4.80 Acres', newVal: '5.50 Acres', status: 'RESOLVED' },
      { field: 'Faculty Professors', oldVal: '0 Professors', newVal: '1 Professor', status: 'RESOLVED' },
      { field: 'Fire NOC Status', oldVal: 'Expired', newVal: 'Renewal In Progress', status: 'MODIFIED' },
    ],
    bodyContent: `SCHEDULE OF PROPERTY (REV 2):
Total land parcel measuring 5.50 Acres (Plots 44/A + 44/B Contiguous).
Cadre Roster: Total 19 faculty members (1 Professor, 4 Associate, 14 Assistant).
Fire Safety: State Fire Dept Renewal Receipt No. RNW-8821 pending final certificate.`,
  },
  {
    version: 3,
    label: 'Rev 3.0 (Final Scrutiny Clearance)',
    date: '2026-10-31 05:10 PM',
    author: 'Scrutiny Committee & Registrar',
    summary: 'Final valid submission. Active Fire NOC renewed through 2029 uploaded and digitally signed.',
    sha256: 'e81a9c...3f10',
    addedText: [
      '+ State Fire Directorate Safety Clearance Certificate No. FSC-2026-0994 valid through 31-Oct-2029.',
      '+ Sub-Registrar Contiguity Certificate confirming single unified educational boundary.',
      '+ Cryptographic QR code stamped by AICTE Scrutiny System.',
    ],
    removedText: [
      '- Provisional Fire Renewal receipt replaced with permanent signed NOC certificate.',
    ],
    paramDiffs: [
      { field: 'Fire NOC Status', oldVal: 'Renewal In Progress', newVal: 'Valid until 2029', status: 'RESOLVED' },
      { field: 'Contiguity Verification', oldVal: 'Pending', newVal: 'Verified & Certified', status: 'RESOLVED' },
      { field: 'Overall Status', oldVal: 'Deficient (Fail)', newVal: 'Compliant (Pass)', status: 'RESOLVED' },
    ],
    bodyContent: `SCHEDULE OF PROPERTY (REV 3 - APPROVED):
Total contiguous land measuring 5.50 Acres duly certified free of encumbrance.
Faculty Cadre: 1 Professor : 4 Associate : 14 Assistant (Compliant with 1:2:6 ratio).
Fire Safety: State Fire Directorate Clearance FSC-2026-0994 valid up to 31-Oct-2029.
AICTE Cryptographic Watermark Verified: 0x8F94D2... VALID.`,
  },
];

export const RevisionTimeMachine: React.FC = () => {
  const [currentRevIndex, setCurrentRevIndex] = useState<number>(REVISIONS.length - 1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const currentRev = REVISIONS[currentRevIndex];

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Revision Time Machine
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-purple-300 font-mono">
                  Diff & Audit Timeline
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Step backwards and forwards through institutional filing revisions with added and removed clauses highlighted.
              </p>
            </div>
          </div>
        </div>

        {/* Current Revision Badge */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs font-bold text-white">{currentRev.label}</div>
            <div className="text-[10px] text-slate-400 font-mono">{currentRev.date}</div>
          </div>
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-purple-950/70 text-purple-300 border border-purple-500/40">
            SHA: {currentRev.sha256}
          </span>
        </div>
      </div>

      {/* Stepper / Slider Controls */}
      <div className="space-y-3 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={currentRevIndex <= 0}
              onClick={() => setCurrentRevIndex((i) => Math.max(i - 1, 0))}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-30"
              title="Previous Revision"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={currentRevIndex >= REVISIONS.length - 1}
              onClick={() => setCurrentRevIndex((i) => Math.min(i + 1, REVISIONS.length - 1))}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-30"
              title="Next Revision"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <span className="text-xs font-mono text-slate-300 font-medium">
            Revision {currentRevIndex + 1} of {REVISIONS.length}
          </span>
        </div>

        {/* Interactive Slider */}
        <input
          type="range"
          min="0"
          max={REVISIONS.length - 1}
          value={currentRevIndex}
          onChange={(e) => setCurrentRevIndex(parseInt(e.target.value))}
          className="w-full accent-purple-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
        />

        {/* Milestone Steps Bar */}
        <div className="grid grid-cols-3 gap-2 pt-1">
          {REVISIONS.map((rev, idx) => {
            const isSelected = idx === currentRevIndex;
            return (
              <button
                key={rev.version}
                type="button"
                onClick={() => setCurrentRevIndex(idx)}
                className={`p-2 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'bg-purple-950/60 border-purple-500/60 ring-2 ring-purple-500/20 text-white'
                    : 'bg-slate-900/40 border-slate-800/80 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-slate-200">{rev.label}</span>
                  <GitCommit className="w-3.5 h-3.5 text-purple-400" />
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">{rev.summary}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Side-by-Side Diff Content & Modifications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Added & Removed Clauses Highlighted */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <FileDiff className="w-4 h-4 text-sky-400" />
            <span>Document Diff Highlights</span>
          </h4>

          {/* Added text */}
          <div className="space-y-2">
            <div className="text-[11px] font-bold uppercase text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Added Text & Clauses in {currentRev.label}
            </div>
            {currentRev.addedText.length > 0 ? (
              <div className="space-y-1.5">
                {currentRev.addedText.map((txt, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 text-xs font-mono"
                  >
                    {txt}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic p-2">None added in this baseline.</div>
            )}
          </div>

          {/* Removed text */}
          <div className="space-y-2">
            <div className="text-[11px] font-bold uppercase text-rose-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              Removed / Superseded Text
            </div>
            {currentRev.removedText.length > 0 ? (
              <div className="space-y-1.5">
                {currentRev.removedText.map((txt, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-500/40 text-rose-300 line-through text-xs font-mono"
                  >
                    {txt}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic p-2">No clauses removed in this revision.</div>
            )}
          </div>
        </div>

        {/* Right side: Parameter Diff Comparison Table & Document Snapshot */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Statutory Parameters Evolution</span>
          </h4>

          {/* Table */}
          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-900 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="p-2.5">Parameter</th>
                  <th className="p-2.5">Previous Value</th>
                  <th className="p-2.5">Revised Value</th>
                  <th className="p-2.5 text-right">State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-mono text-[11px]">
                {currentRev.paramDiffs.map((diff, i) => (
                  <tr key={i} className="hover:bg-slate-900/40">
                    <td className="p-2.5 font-sans font-semibold text-white">{diff.field}</td>
                    <td className="p-2.5 text-rose-400/80 line-through">{diff.oldVal}</td>
                    <td className="p-2.5 text-emerald-400 font-bold">{diff.newVal}</td>
                    <td className="p-2.5 text-right">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                        {diff.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Document Content Box */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-mono space-y-2">
            <div className="text-[11px] font-bold text-slate-400 uppercase">
              Full Text Preview (Revision Snapshot)
            </div>
            <pre className="text-slate-200 whitespace-pre-wrap leading-relaxed text-[11px]">
              {currentRev.bodyContent}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
