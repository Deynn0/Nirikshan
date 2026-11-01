import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2, FileText, CheckCircle2, AlertTriangle, Eye, ShieldCheck, ChevronLeft, ChevronRight, Layers } from 'lucide-react';
import type { Finding } from '../../api/types';
import { TrustLadderBadge } from '../TrustLadderBadge';

interface FactBox {
  id: string;
  findingId?: string;
  page: number;
  label: string;
  value: string;
  trustLevel: string;
  confidence: number;
  x: number; // percentage 0-100
  y: number;
  w: number;
  h: number;
}

interface DocumentViewerProps {
  dossierId: string;
  documentId?: string;
  documentTitle?: string;
  pageCount?: number;
  findings?: Finding[];
  onSelectFinding?: (findingId: string) => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  dossierId,
  documentId = 'doc-sample-1',
  documentTitle = 'Registered Land Sale Deed (Vol-3)',
  pageCount = 3,
  findings = [],
  onSelectFinding,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [activeBoxId, setActiveBoxId] = useState<string | null>('box-1');
  const [showOverlay, setShowOverlay] = useState<boolean>(true);

  // Extracted spatial facts with bounding boxes mapped to findings
  const factBoxes: FactBox[] = [
    {
      id: 'box-1',
      findingId: findings[0]?.finding_id || 'find-land-01',
      page: 1,
      label: 'Campus Land Area',
      value: '5.50 Acres (Contiguous Parcel)',
      trustLevel: 'STATUTORY_DATABASE',
      confidence: 0.98,
      x: 22,
      y: 28,
      w: 48,
      h: 8,
    },
    {
      id: 'box-2',
      findingId: 'find-survey-02',
      page: 1,
      label: 'Survey / Khasra No.',
      value: 'Survey No. 44/A, Village Rampur',
      trustLevel: 'CRYPTOGRAPHIC_PROOF',
      confidence: 0.99,
      x: 20,
      y: 39,
      w: 52,
      h: 7,
    },
    {
      id: 'box-3',
      findingId: findings[1]?.finding_id || 'find-subregistrar-03',
      page: 2,
      label: 'Sub-Registrar Digital Seal',
      value: 'Sub-Registrar Seal Verified (DSig Valid)',
      trustLevel: 'CRYPTOGRAPHIC_PROOF',
      confidence: 1.0,
      x: 62,
      y: 68,
      w: 28,
      h: 18,
    },
    {
      id: 'box-4',
      findingId: 'find-model-04',
      page: 2,
      label: 'OCR Model Text Extractor',
      value: 'Extracted Clauses 4.1 & 7.2',
      trustLevel: 'MODEL_PREDICTION',
      confidence: 0.84,
      x: 18,
      y: 18,
      w: 64,
      h: 10,
    },
  ];

  const currentPageBoxes = factBoxes.filter((b) => b.page === currentPage);
  const activeBox = factBoxes.find((b) => b.id === activeBoxId);

  const jumpToFinding = (fId: string) => {
    const targetBox = factBoxes.find((b) => b.findingId === fId || b.id === fId);
    if (targetBox) {
      setCurrentPage(targetBox.page);
      setActiveBoxId(targetBox.id);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left/Main Viewer Area */}
      <div className="lg:col-span-8 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-400" />
            <div>
              <h3 className="text-sm font-bold text-white truncate max-w-[260px] sm:max-w-md">
                {documentTitle}
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                pdf.js Canvas Overlay • {pageCount} Pages • Document ID: {documentId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Page navigation */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs text-slate-300">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                className="p-1 hover:text-white disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-mono text-[11px]">
                {currentPage} / {pageCount}
              </span>
              <button
                type="button"
                disabled={currentPage >= pageCount}
                onClick={() => setCurrentPage((p) => Math.min(p + 1, pageCount))}
                className="p-1 hover:text-white disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs text-slate-300">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(z - 15, 70))}
                className="p-1 hover:text-white"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="px-1.5 font-mono text-[11px]">{zoomLevel}%</span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(z + 15, 150))}
                className="p-1 hover:text-white"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Toggle Overlay */}
            <button
              type="button"
              onClick={() => setShowOverlay(!showOverlay)}
              className={`p-1.5 rounded-lg border text-xs transition-colors flex items-center gap-1 ${
                showOverlay
                  ? 'bg-sky-500/20 border-sky-500/40 text-sky-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
              title="Toggle Bounding Boxes"
            >
              <Layers className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Document Canvas Container */}
        <div className="relative w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800/80 min-h-[520px] flex items-center justify-center p-4">
          <div
            className="relative bg-white text-slate-900 shadow-2xl rounded-sm transition-transform duration-200"
            style={{
              width: `${(620 * zoomLevel) / 100}px`,
              minHeight: `${(780 * zoomLevel) / 100}px`,
              fontFamily: 'serif',
            }}
          >
            {/* Simulated High-Fidelity Official Document Page Content */}
            <div className="p-8 sm:p-12 text-[13px] leading-relaxed select-text space-y-4">
              <div className="text-center pb-4 border-b border-slate-300">
                <div className="text-xs uppercase font-sans font-bold tracking-widest text-slate-500">
                  Government of National Capital Territory of Delhi
                </div>
                <div className="text-base font-bold font-serif text-slate-900 uppercase mt-1">
                  Department of Revenue & Land Registration
                </div>
                <div className="text-[11px] text-slate-600 font-sans mt-0.5">
                  Book 1, Volume 384, Pages 112–126 • Registration Deed No. 4482/2024
                </div>
              </div>

              {currentPage === 1 && (
                <>
                  <div className="text-center font-bold text-sm underline uppercase tracking-wide">
                    Deed of Absolute Sale & Transfer of Contiguous Land
                  </div>
                  <p className="text-justify text-slate-800 indent-8">
                    THIS INDENTURE is made and entered into on this 14th day of March, 2024, by and between
                    M/s Sunrise Educational Society (hereinafter termed the PURCHASER) and the statutory vendors.
                  </p>
                  <p className="text-justify text-slate-800 indent-8">
                    WHEREAS the Purchaser has applied for establishment of an AICTE approved Technical Engineering
                    Campus under Approval Process Handbook norms, requiring statutory possession of contiguous land.
                  </p>
                  <div className="p-3 bg-amber-50/50 border border-amber-200/80 rounded my-2 text-xs">
                    <p className="font-bold text-slate-900">
                      SCHEDULE OF PROPERTY CONVEYED:
                    </p>
                    <p className="mt-1">
                      Total land measuring <span className="font-bold underline">5.50 Acres</span> (equivalent to 22,257.7 square meters)
                      situated in Khasra / Survey No. <span className="font-bold underline">44/A</span>, Revenue Village Rampur, Sub-District South.
                    </p>
                  </div>
                  <p className="text-justify text-slate-800 indent-8">
                    The vendor guarantees that the conveyed land parcel is free from all encumbrances, liens, mortgages,
                    charges, and litigation whatsoever, and forms a single unified piece suitable for higher education.
                  </p>
                </>
              )}

              {currentPage === 2 && (
                <>
                  <div className="text-center font-bold text-sm underline uppercase tracking-wide">
                    Execution, Boundaries & Digital Attestation
                  </div>
                  <p className="text-justify text-slate-800 indent-8">
                    BOUNDARIES: North: 60-feet Main Sector Arterial Road; South: Survey Plot 45;
                    East: Government Green Belt; West: Revenue Drain & Survey 43.
                  </p>
                  <p className="text-justify text-slate-800 indent-8">
                    The Purchaser undertakes to adhere strictly to statutory educational land use and will not partition,
                    alienate, or sublease the land without prior written approval from AICTE.
                  </p>
                  <div className="mt-12 flex justify-between items-end pt-8 border-t border-slate-300">
                    <div className="text-xs">
                      <p className="font-bold">Authorized Signatory</p>
                      <p className="text-slate-500">For Sunrise Educational Trust</p>
                    </div>
                    <div className="text-right text-xs">
                      <div className="w-28 h-20 border-2 border-indigo-700/60 rounded flex flex-col items-center justify-center p-1 bg-indigo-50/60 text-indigo-900 font-sans text-[10px]">
                        <span className="font-bold uppercase tracking-wider">Sub-Registrar</span>
                        <span>Digital Seal</span>
                        <span className="text-[9px] font-mono mt-0.5">SHA-256 Valid</span>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {currentPage === 3 && (
                <>
                  <div className="text-center font-bold text-sm underline uppercase tracking-wide">
                    Revenue Enclosure & Survey Map Extract
                  </div>
                  <div className="h-64 border-2 border-dashed border-slate-300 rounded flex items-center justify-center text-slate-400 font-sans text-xs">
                    Cadastral Survey Map Extract — Contiguous Geo-Polygon Sheet
                  </div>
                </>
              )}
            </div>

            {/* Interactive Bounding Boxes Overlay */}
            {showOverlay &&
              currentPageBoxes.map((box) => {
                const isActive = box.id === activeBoxId;
                const isModel = box.trustLevel === 'MODEL_PREDICTION';

                return (
                  <div
                    key={box.id}
                    onClick={() => setActiveBoxId(box.id)}
                    style={{
                      left: `${box.x}%`,
                      top: `${box.y}%`,
                      width: `${box.w}%`,
                      height: `${box.h}%`,
                    }}
                    className={`absolute cursor-pointer rounded transition-all duration-200 select-none group ${
                      isActive
                        ? 'border-2 border-sky-400 bg-sky-500/20 ring-4 ring-sky-400/30 z-20 shadow-lg'
                        : isModel
                        ? 'border-2 border-amber-500/80 bg-amber-500/10 hover:bg-amber-500/20 z-10'
                        : 'border-2 border-indigo-500/80 bg-indigo-500/10 hover:bg-indigo-500/20 z-10'
                    }`}
                  >
                    {/* Badge on Box */}
                    <div
                      className={`absolute -top-3 left-1 px-1.5 py-0.2 rounded text-[9px] font-sans font-bold shadow ${
                        isActive
                          ? 'bg-sky-500 text-white'
                          : isModel
                          ? 'bg-amber-600 text-white'
                          : 'bg-indigo-600 text-white'
                      }`}
                    >
                      {box.label} {isModel && '(Advisory)'}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* Right Findings & Bounding Box Details Panel */}
      <div className="lg:col-span-4 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-5">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Extracted Facts & Findings</span>
            <span className="text-[10px] text-sky-400 font-mono">Click to Jump</span>
          </h4>
          <p className="text-xs text-slate-400 mt-1">
            Click any verified finding to jump directly to its bounding box region in the document viewer.
          </p>
        </div>

        {/* Fact list items */}
        <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
          {factBoxes.map((box) => {
            const isActive = box.id === activeBoxId;

            return (
              <div
                key={box.id}
                onClick={() => jumpToFinding(box.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  isActive
                    ? 'bg-sky-950/40 border-sky-500/60 ring-2 ring-sky-500/20 shadow-md'
                    : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-bold text-white">{box.label}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                    Page {box.page}
                  </span>
                </div>
                <div className="text-xs text-slate-200 mt-1 font-medium">{box.value}</div>
                <div className="mt-2.5 flex items-center justify-between">
                  <TrustLadderBadge
                    level={box.trustLevel}
                    size="sm"
                    isModelAdvisory={box.trustLevel === 'MODEL_PREDICTION'}
                  />
                  <span className="text-[10px] font-mono text-emerald-400">
                    {(box.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Box Inspection Drawer */}
        {activeBox && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-slate-400 font-mono text-[11px]">
              <span>Active Bounding Box Inspection</span>
              <span className="text-sky-400">Page {activeBox.page}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-500">Bounding Box X/Y:</span>
                <p className="font-mono text-slate-300">{activeBox.x}%, {activeBox.y}%</p>
              </div>
              <div>
                <span className="text-slate-500">Box Dimension W/H:</span>
                <p className="font-mono text-slate-300">{activeBox.w}% × {activeBox.h}%</p>
              </div>
            </div>
            <div className="pt-1">
              <span className="text-slate-500">Statutory Grounding:</span>
              <p className="text-slate-300 mt-0.5 font-sans">
                Mapped to AICTE APH 2024-2027 Rule Engine with spatial OCR validation.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
