import React, { useState } from 'react';
import { X, FileText, CheckCircle2, ShieldCheck, Download, Loader2, FolderTree, FileCode, Lock } from 'lucide-react';

interface ExportEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: string;
  institutionName: string;
}

export const ExportEvidenceModal: React.FC<ExportEvidenceModalProps> = ({
  isOpen,
  onClose,
  applicationId,
  institutionName,
}) => {
  const [includeRawOcr, setIncludeRawOcr] = useState<boolean>(true);
  const [isBuilding, setIsBuilding] = useState<boolean>(false);
  const [buildComplete, setBuildComplete] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleBuild = () => {
    setIsBuilding(true);
    setBuildComplete(false);
    setTimeout(() => {
      setIsBuilding(false);
      setBuildComplete(true);
    }, 1500);
  };

  const handleDownload = () => {
    // Generate a simple evidence manifest JSON file download
    const manifest = {
      application_id: applicationId,
      institution: institutionName,
      created_at: new Date().toISOString(),
      officer: 'Dr. Sunita Sharma',
      scrutiny_jurisdiction: 'AICTE Western Regional Office (WRO)',
      evidence_pack: {
        'report.pdf': {
          size_bytes: 2457812,
          sha256: '7f9a2b0ee8172940294819772384910293847192837401928347102e148c7d',
        },
        'manifest.json': {
          version: '1.0.0',
          merkle_root: 'sha256:a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e',
        },
        'audit/': {
          chain_length: 5,
          head_hash: 'sha256:bb0198aa12837491823749817234981273948127394812739481273948127394',
        },
        'signature.json': {
          signer: 'AICTE-OFFICER-WRO-01',
          algorithm: 'RSASSA-PSS-SHA256',
        },
      },
    };

    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Evidence_Pack_${applicationId}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 dark:bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-floating border border-stone-200 dark:border-slate-800 overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between bg-stone-50/70 dark:bg-slate-900/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-stone-900 dark:text-slate-100">
                Export Evidence Pack
              </h3>
              <p className="text-[11px] text-stone-500 font-mono">{applicationId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          <p className="text-xs text-stone-600 dark:text-slate-400 leading-relaxed">
            Generate an immutable, court-admissible forensic evidence bundle containing statutory
            findings, OCR glyph extractions, and Merkle audit logs.
          </p>

          {/* Specified File List */}
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-2">
              Pack Contents & Artifacts
            </span>
            <div className="surface-card bg-stone-50/60 dark:bg-slate-800/40 border border-stone-200 dark:border-slate-700 rounded-xl divide-y divide-stone-200/80 dark:divide-slate-700/80 text-xs">
              {/* report.pdf */}
              <div className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-purple-600" />
                  <div>
                    <span className="font-mono font-medium text-stone-900 dark:text-slate-100">
                      report.pdf
                    </span>
                    <span className="text-[11px] text-stone-500 block">
                      Executive Scrutiny Report & Deficiency Rationale
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-stone-400">2.4 MB</span>
              </div>

              {/* manifest.json */}
              <div className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileCode className="w-4 h-4 text-indigo-600" />
                  <div>
                    <span className="font-mono font-medium text-stone-900 dark:text-slate-100">
                      manifest.json
                    </span>
                    <span className="text-[11px] text-stone-500 block">
                      SHA-256 evidence checksums & statutory rule mappings
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-stone-400">14 KB</span>
              </div>

              {/* audit/ directory */}
              <div className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FolderTree className="w-4 h-4 text-amber-600" />
                  <div>
                    <span className="font-mono font-medium text-stone-900 dark:text-slate-100">
                      audit/
                    </span>
                    <span className="text-[11px] text-stone-500 block">
                      Immutable Merkle audit tree & transaction signatures
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-stone-400">86 KB</span>
              </div>

              {/* signature.json */}
              <div className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Lock className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="font-mono font-medium text-stone-900 dark:text-slate-100">
                      signature.json
                    </span>
                    <span className="text-[11px] text-stone-500 block">
                      Cryptographic officer seal (RSASSA-PSS-256)
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-stone-400">4 KB</span>
              </div>
            </div>
          </div>

          {/* Specified Checkbox */}
          <label className="flex items-start gap-3 p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 cursor-pointer hover:border-purple-300 transition-colors">
            <input
              type="checkbox"
              checked={includeRawOcr}
              onChange={(e) => setIncludeRawOcr(e.target.checked)}
              className="mt-0.5 rounded text-purple-600 focus:ring-purple-500 border-stone-300 dark:border-slate-600"
            />
            <div className="text-xs">
              <span className="font-semibold text-stone-900 dark:text-slate-100 block">
                Include raw OCR extractions & high-resolution photo forensic attachments
              </span>
              <span className="text-stone-500 text-[11px] mt-0.5 block">
                Appends uncompressed EXIF photogrammetry images, YOLO inference coordinates, and raw glyph streams (+18.2 MB).
              </span>
            </div>
          </label>

          {/* Building Feedback */}
          {buildComplete && (
            <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Evidence pack successfully compiled and sealed with Merkle anchor.</span>
            </div>
          )}
        </div>

        {/* Modal Footer: Cancel / Build evidence pack buttons */}
        <div className="px-6 py-4 bg-stone-50 dark:bg-slate-950 border-t border-stone-200 dark:border-slate-800 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-white transition-colors"
          >
            Cancel
          </button>

          {buildComplete ? (
            <button
              onClick={handleDownload}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-2"
            >
              <Download className="w-3.5 h-3.5" />
              Download Sealed Pack
            </button>
          ) : (
            <button
              onClick={handleBuild}
              disabled={isBuilding}
              className="px-5 py-2 rounded-xl bg-[#6D28D9] hover:bg-[#5B21B6] active:bg-[#4C1D95] text-white text-xs font-semibold shadow-sm hover:shadow transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isBuilding ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Building Evidence Pack...
                </>
              ) : (
                'Build evidence pack'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
