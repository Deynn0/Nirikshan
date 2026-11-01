import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  HelpCircle,
  Gavel,
  Download,
  AlertTriangle,
  FileText,
  Layers,
  Camera,
  History,
  CheckCircle2,
  XCircle,
  ExternalLink,
  MapPin,
  Calendar,
  Building,
  Check,
  Eye,
  Sparkles,
  Info,
} from 'lucide-react';
import { PillBadge } from '../../components/common/PillBadge';
import {
  mockApplications,
  mockProofStrengthRows,
  mockFindings,
  mockCertCoverage,
  mockAuditTrail,
  FindingDetail,
} from '../../data/mockScrutinyData';
import { AskWhyDrawer } from '../../components/workspace/AskWhyDrawer';
import { ExportEvidenceModal } from '../../components/workspace/ExportEvidenceModal';

export const ApplicationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const appId = id || 'APP-2026-AICTE-4891';
  const appData =
    mockApplications.find((a) => a.id === appId) || mockApplications[0];

  // Active Tab: Summary, Findings, Documents, Comparisons, Activity
  const [activeTab, setActiveTab] = useState<
    'SUMMARY' | 'FINDINGS' | 'DOCUMENTS' | 'COMPARISONS' | 'ACTIVITY'
  >('SUMMARY');

  // Modals & Drawers
  const [isAskWhyOpen, setIsAskWhyOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isDecideOpen, setIsDecideOpen] = useState(false);
  const [decisionFeedback, setDecisionFeedback] = useState<string | null>(null);

  // Findings selection
  const [selectedFinding, setSelectedFinding] = useState<FindingDetail>(mockFindings[0]);
  const [activeDocPage, setActiveDocPage] = useState<number>(4);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState<boolean>(true);

  // Group findings into Validity, Verification, Document forensics
  const validityFindings = mockFindings.filter((f) => f.group === 'Validity');
  const verificationFindings = mockFindings.filter((f) => f.group === 'Verification');
  const forensicFindings = mockFindings.filter((f) => f.group === 'Document forensics');

  const handleShowOnPage = (docName: string, pageNum: number) => {
    setActiveDocPage(pageNum);
    setActiveTab('DOCUMENTS');
  };

  const handleDecisionSubmit = (action: string) => {
    setDecisionFeedback(`Decision recorded: ${action}. Sent to Joint Scrutiny Board.`);
    setTimeout(() => {
      setIsDecideOpen(false);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* 1. Header with Institution Name, Status Badge, ID, Location, Ask Why and Decide */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-6 shadow-soft">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
              <h1 className="text-xl sm:text-2xl font-extrabold text-stone-900 dark:text-white tracking-tight">
                {appData.name}
              </h1>
              <PillBadge
                variant={
                  appData.statusType === 'critical'
                    ? 'critical'
                    : appData.statusType === 'warning'
                    ? 'warning'
                    : 'verified'
                }
                dot
              >
                {appData.status}
              </PillBadge>
              <PillBadge variant="violet" size="sm">
                E4 Digilocker
              </PillBadge>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-stone-500 font-sans">
              <span className="font-mono bg-stone-100 dark:bg-slate-800 px-2 py-0.5 rounded text-stone-700 dark:text-slate-300">
                {appData.id}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-stone-400" />
                {appData.location}
              </span>
              <span className="flex items-center gap-1">
                <Building className="w-3.5 h-3.5 text-stone-400" />
                {appData.category} Directorate
              </span>
              <span className="flex items-center gap-1 font-mono text-[11px]">
                <Calendar className="w-3.5 h-3.5 text-stone-400" />
                Cycle: 2026–2027
              </span>
            </div>
          </div>

          {/* Action Buttons: Ask Why, Decide, Export */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setIsAskWhyOpen(true)}
              className="px-4 py-2 rounded-xl bg-purple-50 dark:bg-purple-950/40 hover:bg-purple-100 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs"
            >
              <HelpCircle className="w-4 h-4" />
              Ask why
            </button>

            <button
              onClick={() => setIsExportOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-stone-100 dark:bg-slate-800 hover:bg-stone-200 dark:hover:bg-slate-700 text-stone-700 dark:text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <Download className="w-4 h-4" />
              Evidence pack
            </button>

            <button
              onClick={() => setIsDecideOpen(true)}
              className="px-5 py-2 rounded-xl bg-[#6D28D9] hover:bg-[#5B21B6] active:bg-[#4C1D95] text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm hover:shadow transition-all"
            >
              <Gavel className="w-4 h-4" />
              Decide
            </button>
          </div>
        </div>

        {/* 2. Navigation Tabs */}
        <div className="flex items-center gap-2 mt-6 border-t border-stone-200 dark:border-slate-800 pt-3 overflow-x-auto">
          <button
            onClick={() => setActiveTab('SUMMARY')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'SUMMARY'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Summary
          </button>

          <button
            onClick={() => setActiveTab('FINDINGS')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'FINDINGS'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
            Findings ({mockFindings.length})
          </button>

          <button
            onClick={() => setActiveTab('DOCUMENTS')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'DOCUMENTS'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Documents
          </button>

          <button
            onClick={() => setActiveTab('COMPARISONS')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'COMPARISONS'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-slate-200'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            Comparisons
          </button>

          <button
            onClick={() => setActiveTab('ACTIVITY')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
              activeTab === 'ACTIVITY'
                ? 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                : 'text-stone-600 dark:text-slate-400 hover:text-stone-900 dark:hover:text-slate-200'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Activity
          </button>
        </div>
      </div>

      {/* 3. Tab Contents */}

      {/* TAB 1: SUMMARY */}
      {activeTab === 'SUMMARY' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Proof Strength Grid (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
              <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800 mb-4">
                <div>
                  <h3 className="font-bold text-sm text-stone-900 dark:text-slate-100">
                    Proof Strength Grid
                  </h3>
                  <p className="text-xs text-stone-500">
                    Multilateral cross-examination: Declared vs Present, OCR Read, AICTE Record, Sovereign Registry, and Signature/QR
                  </p>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                    <span className="w-2.5 h-1.5 bg-emerald-500 rounded-xs" /> Verified
                  </span>
                  <span className="flex items-center gap-1 text-amber-600 font-semibold">
                    <span className="w-2.5 h-1.5 bg-amber-500 rounded-xs" /> Warning
                  </span>
                  <span className="flex items-center gap-1 text-rose-600 font-semibold">
                    <span className="w-2.5 h-1.5 bg-rose-500 rounded-xs" /> Contradicted
                  </span>
                </div>
              </div>

              {/* Grid Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-stone-50 dark:bg-slate-900/60 text-[10px] uppercase font-semibold text-stone-400 border-b border-stone-200 dark:border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Statutory Requirement</th>
                      <th className="py-2.5 px-2 text-center">Declared</th>
                      <th className="py-2.5 px-2 text-center">Present</th>
                      <th className="py-2.5 px-2 text-center">Read</th>
                      <th className="py-2.5 px-2 text-center">AICTE Record</th>
                      <th className="py-2.5 px-2 text-center">Issuer Reg.</th>
                      <th className="py-2.5 px-2 text-center">Sig/QR</th>
                      <th className="py-2.5 px-3">Strongest Proof</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
                    {mockProofStrengthRows.map((row, idx) => {
                      const renderBar = (color: 'green' | 'amber' | 'red' | 'gray') => {
                        let bg = 'bg-stone-300 dark:bg-slate-700';
                        if (color === 'green') bg = 'bg-emerald-500';
                        if (color === 'amber') bg = 'bg-amber-500';
                        if (color === 'red') bg = 'bg-rose-500';

                        return (
                          <div className="flex justify-center">
                            <span className={`w-5 h-2 rounded-xs ${bg}`} />
                          </div>
                        );
                      };

                      return (
                        <tr
                          key={idx}
                          className="hover:bg-stone-50/70 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="py-3 px-3 font-medium text-stone-900 dark:text-slate-100">
                            {row.requirement}
                          </td>
                          <td className="py-3 px-2">{renderBar(row.declared)}</td>
                          <td className="py-3 px-2">{renderBar(row.present)}</td>
                          <td className="py-3 px-2">{renderBar(row.read)}</td>
                          <td className="py-3 px-2">{renderBar(row.aicteRecord)}</td>
                          <td className="py-3 px-2">{renderBar(row.issuerRegistry)}</td>
                          <td className="py-3 px-2">{renderBar(row.signatureQr)}</td>
                          <td className="py-3 px-3">
                            <span className="font-mono text-[11px] text-stone-600 dark:text-slate-300 block">
                              {row.strongestProof}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Column: Institution Details, Declared Figures & Timeline Chart (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Institution Details & Declared Figures */}
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-3">
                Institution Profile & Declared Figures
              </span>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-stone-400 text-[10px] uppercase block">Sponsoring Trust</span>
                  <span className="font-semibold text-stone-900 dark:text-white">
                    Vidya Vikas Pratishthan Trust (Reg MAH/782/2004)
                  </span>
                </div>
                <div>
                  <span className="text-stone-400 text-[10px] uppercase block">University Affiliation</span>
                  <span className="font-semibold text-stone-900 dark:text-white">
                    Savitribai Phule Pune University (SPPU)
                  </span>
                </div>
                <div>
                  <span className="text-stone-400 text-[10px] uppercase block">Campus Cadastre</span>
                  <span className="font-mono text-stone-700 dark:text-slate-300">
                    Plot 42/1A & 42/2, Taluka Haveli, Pune
                  </span>
                </div>

                {/* Declared Stat Metrics */}
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-stone-100 dark:border-slate-800">
                  <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/50">
                    <span className="text-[10px] uppercase text-stone-400 block">Faculty</span>
                    <strong className="text-sm text-stone-900 dark:text-white">64 teachers</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/50">
                    <span className="text-[10px] uppercase text-stone-400 block">Campus Land</span>
                    <strong className="text-sm text-stone-900 dark:text-white">9.61 acres</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/50">
                    <span className="text-[10px] uppercase text-stone-400 block">Built-up Carpet</span>
                    <strong className="text-sm text-stone-900 dark:text-white">12,450 sqm</strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/50">
                    <span className="text-[10px] uppercase text-stone-400 block">Sanctioned Intake</span>
                    <strong className="text-sm text-stone-900 dark:text-white">360 seats</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Certificate-Coverage Timeline Chart */}
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-3">
                Certificate-Coverage Timeline Chart
              </span>

              <div className="space-y-3.5">
                {mockCertCoverage.map((cert, i) => {
                  let barColor = 'bg-emerald-500';
                  let pillVariant: 'verified' | 'warning' | 'critical' = 'verified';

                  if (cert.status === 'warning') {
                    barColor = 'bg-amber-500';
                    pillVariant = 'warning';
                  } else if (cert.status === 'critical') {
                    barColor = 'bg-rose-500';
                    pillVariant = 'critical';
                  }

                  return (
                    <div key={i} className="text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-stone-800 dark:text-slate-200">
                          {cert.name}
                        </span>
                        <PillBadge variant={pillVariant} size="sm">
                          {cert.note}
                        </PillBadge>
                      </div>

                      {/* Visual Span Bar */}
                      <div className="h-2 w-full bg-stone-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          style={{
                            width:
                              cert.status === 'critical'
                                ? '40%'
                                : cert.status === 'warning'
                                ? '65%'
                                : '92%',
                          }}
                          className={`h-full rounded-full ${barColor}`}
                        />
                      </div>

                      <div className="flex justify-between text-[10px] font-mono text-stone-400 mt-0.5">
                        <span>{cert.start}</span>
                        <span>{cert.end}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: FINDINGS */}
      {activeTab === 'FINDINGS' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Grouped Findings List (5 cols) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Validity Group */}
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft">
              <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400 block mb-2">
                Validity Group ({validityFindings.length})
              </span>
              <div className="space-y-2">
                {validityFindings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      selectedFinding.id === f.id
                        ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-400 dark:border-purple-600 shadow-sm item-selected-orange'
                        : 'bg-stone-50/50 dark:bg-slate-800/30 border-stone-200 dark:border-slate-800 hover:border-stone-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-semibold text-xs text-stone-900 dark:text-slate-100 line-clamp-1">
                        {f.title}
                      </span>
                      <PillBadge
                        variant={f.severity === 'critical' ? 'critical' : 'warning'}
                        size="sm"
                      >
                        {f.severityLabel}
                      </PillBadge>
                    </div>
                    <p className="text-[11px] text-stone-500 font-mono">{f.ruleId}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Verification Group */}
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft">
              <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400 block mb-2">
                Verification Group ({verificationFindings.length})
              </span>
              <div className="space-y-2">
                {verificationFindings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      selectedFinding.id === f.id
                        ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-400 dark:border-purple-600 shadow-sm item-selected-orange'
                        : 'bg-stone-50/50 dark:bg-slate-800/30 border-stone-200 dark:border-slate-800 hover:border-stone-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-semibold text-xs text-stone-900 dark:text-slate-100 line-clamp-1">
                        {f.title}
                      </span>
                      <PillBadge
                        variant={f.severity === 'critical' ? 'critical' : 'warning'}
                        size="sm"
                      >
                        {f.severityLabel}
                      </PillBadge>
                    </div>
                    <p className="text-[11px] text-stone-500 font-mono">{f.ruleId}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Document Forensics Group */}
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft">
              <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400 block mb-2">
                Document Forensics Group ({forensicFindings.length})
              </span>
              <div className="space-y-2">
                {forensicFindings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      selectedFinding.id === f.id
                        ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-400 dark:border-purple-600 shadow-sm item-selected-orange'
                        : 'bg-stone-50/50 dark:bg-slate-800/30 border-stone-200 dark:border-slate-800 hover:border-stone-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-semibold text-xs text-stone-900 dark:text-slate-100 line-clamp-1">
                        {f.title}
                      </span>
                      <PillBadge
                        variant={f.severity === 'critical' ? 'critical' : 'warning'}
                        size="sm"
                      >
                        {f.severityLabel}
                      </PillBadge>
                    </div>
                    <p className="text-[11px] text-stone-500 font-mono">{f.ruleId}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Finding Detail Panel with Evidence Rows & Show on page link (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-6 shadow-soft space-y-5">
              <div className="flex items-start justify-between gap-3 pb-4 border-b border-stone-200 dark:border-slate-800">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs font-bold text-purple-700 dark:text-purple-400">
                      {selectedFinding.ruleId}
                    </span>
                    <PillBadge
                      variant={selectedFinding.severity === 'critical' ? 'critical' : 'warning'}
                      size="sm"
                    >
                      {selectedFinding.severityLabel}
                    </PillBadge>
                    <span className="text-[11px] text-stone-400 font-sans">
                      Category: {selectedFinding.group}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-stone-900 dark:text-white">
                    {selectedFinding.title}
                  </h3>
                </div>

                {/* Show on Page Link */}
                <button
                  onClick={() =>
                    handleShowOnPage(selectedFinding.documentRef, selectedFinding.pageNumber)
                  }
                  className="px-3 py-1.5 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] text-white text-xs font-semibold flex items-center gap-1.5 shrink-0 shadow-xs"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Show on page
                </button>
              </div>

              {/* Description & Recommendation */}
              <div className="space-y-3 text-xs leading-relaxed">
                <div>
                  <span className="font-semibold text-stone-900 dark:text-slate-100 block mb-1">
                    Deficiency Finding
                  </span>
                  <p className="text-stone-600 dark:text-slate-300">
                    {selectedFinding.description}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-stone-50 dark:bg-slate-800/60 border border-stone-200 dark:border-slate-700">
                  <span className="font-semibold text-purple-900 dark:text-purple-300 block mb-0.5">
                    Recommended Scrutiny Action
                  </span>
                  <p className="text-stone-600 dark:text-slate-400">
                    {selectedFinding.recommendation}
                  </p>
                </div>
              </div>

              {/* Evidence Rows */}
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-2">
                  Tamper-Evident Evidence Extractions
                </span>

                <div className="border border-stone-200 dark:border-slate-800 rounded-xl p-4 bg-stone-50/50 dark:bg-slate-800/40 space-y-3 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-stone-200 dark:border-slate-700 font-mono text-[11px]">
                    <span className="text-stone-600 dark:text-slate-300">
                      Doc: {selectedFinding.documentRef}
                    </span>
                    <span className="text-purple-600 font-bold">
                      Page {selectedFinding.pageNumber}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase text-stone-400 block mb-1">
                      Exact Glyph Stream / OCR Excerpt
                    </span>
                    <p className="font-mono text-xs bg-white dark:bg-slate-900 p-3 rounded-lg border border-stone-200 dark:border-slate-700 text-stone-800 dark:text-slate-200">
                      {selectedFinding.evidenceSnippet}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-[10px] font-mono text-stone-400 pt-1">
                    <span>Evidence Hash: {selectedFinding.evidenceHash}</span>
                    <span>Statute: {selectedFinding.statutoryReference}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DOCUMENTS */}
      {activeTab === 'DOCUMENTS' && (
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-6 shadow-soft space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-stone-200 dark:border-slate-800">
            <div>
              <h3 className="font-bold text-sm text-stone-900 dark:text-slate-100">
                Document Forensics Viewer
              </h3>
              <p className="text-xs text-stone-500 font-mono">
                Viewing: Registered_Lease_Deed_SubRegistrar_Pune.pdf · Page {activeDocPage}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-stone-500">Page:</span>
              <input
                type="number"
                value={activeDocPage}
                onChange={(e) => setActiveDocPage(Number(e.target.value))}
                className="w-16 px-2 py-1 text-xs border rounded bg-stone-50 dark:bg-slate-800 text-center font-mono"
              />
              <PillBadge variant="critical" size="sm">
                Clause 4.1.2 Highlighted
              </PillBadge>
            </div>
          </div>

          {/* High Fidelity Document Canvas Simulation */}
          <div className="p-8 bg-stone-100 dark:bg-slate-950 rounded-xl border border-stone-300 dark:border-slate-800 flex justify-center">
            <div className="w-full max-w-2xl bg-white dark:bg-slate-900 p-8 rounded-lg shadow-md border border-stone-300 dark:border-slate-700 space-y-4 text-xs font-serif leading-relaxed text-stone-800 dark:text-slate-200 select-text">
              <div className="text-center border-b border-stone-300 pb-3 font-sans">
                <h4 className="font-bold uppercase tracking-wider text-sm">
                  Sub-Registrar Office, Haveli No. 4, District Pune
                </h4>
                <p className="text-[10px] text-stone-500 font-mono">
                  Registered Lease Deed Index-II · Registration No: 4192/2014
                </p>
              </div>

              <p>
                THIS INDENTURE OF LEASE made and entered into on this 1st day of April 2014 between
                Shri Jagtap Enterprises (Lessor) and Vidya Vikas Pratishthan Trust (Lessee)...
              </p>

              {/* Highlighted Clause Box */}
              <div className="p-4 rounded-lg border-2 border-rose-500 bg-rose-50/50 dark:bg-rose-950/20 text-rose-950 dark:text-rose-200 font-sans my-4 relative">
                <span className="absolute -top-2.5 left-3 px-2 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-bold uppercase font-sans">
                  Forensic Discrepancy (Clause 4.1)
                </span>
                <p className="font-semibold text-xs">
                  "...to have and to hold the said demised campus plot admeasuring 9.61 acres for a
                  term of twenty-five (25) continuous years commencing from April 2014 to March 2039..."
                </p>
                <p className="text-[11px] text-rose-700 dark:text-rose-300 mt-2 font-mono">
                  Statutory Rule: AICTE mandates minimum 30-year active lease on scrutiny date. Only 18 years remain.
                </p>
              </div>

              <p>
                AND THE LESSEE covenants to keep all instructional laboratories, administrative blocks,
                and playground facilities in proper condition throughout the tenure...
              </p>

              <div className="pt-6 border-t border-stone-200 dark:border-slate-800 flex items-center justify-between font-sans text-[11px] text-stone-500">
                <span>Sub-Registrar Digital Seal Verified</span>
                <span className="font-mono">SHA-256: 4d83e2f1839a829104ebc7612c77d940</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: COMPARISONS */}
      {activeTab === 'COMPARISONS' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Photo with Detection Boxes & Room check result (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
              <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800 mb-4">
                <div>
                  <h3 className="font-bold text-sm text-stone-900 dark:text-slate-100 flex items-center gap-2">
                    Physical Campus Photo vs AI Computer Vision
                    <PillBadge variant="verified" size="sm">
                      Room Check Passed
                    </PillBadge>
                  </h3>
                  <p className="text-xs text-stone-500">
                    High-resolution inspector photo evaluated with YOLOv8 object detection model
                  </p>
                </div>
                <button
                  onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                  className="px-3 py-1 rounded-lg text-xs font-semibold border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 hover:bg-stone-100"
                >
                  {showBoundingBoxes ? 'Hide Bounding Boxes' : 'Show Bounding Boxes'}
                </button>
              </div>

              {/* Photo Container with Bounding Boxes */}
              <div className="relative w-full aspect-[16/10] bg-stone-900 rounded-xl overflow-hidden border border-stone-300 dark:border-slate-700 select-none">
                {/* Simulated Computer Lab Background Image */}
                <div className="absolute inset-0 bg-gradient-to-tr from-slate-900 via-indigo-950 to-slate-800 flex items-center justify-center">
                  <div className="text-center text-slate-400 space-y-2 p-6">
                    <Camera className="w-10 h-10 mx-auto text-purple-400 opacity-60" />
                    <p className="font-mono text-xs text-slate-300">
                      HIGH-DENSITY COMPUTING LAB 04 · APEX INSTITUTE PUNE
                    </p>
                    <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                      68 Core i7 Workstations, Dual 10Gbps CISCO Core Switches, Smoke & Sprinkler Egress
                    </p>
                  </div>
                </div>

                {/* Bounding Box Overlays */}
                {showBoundingBoxes && (
                  <>
                    {/* Box 1: Workstation Cluster */}
                    <div className="absolute top-[20%] left-[12%] w-[48%] h-[52%] border-2 border-emerald-400 bg-emerald-500/10 rounded">
                      <span className="absolute -top-5 left-0 bg-emerald-600 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                        Workstations x68 [0.96]
                      </span>
                    </div>

                    {/* Box 2: Server Rack */}
                    <div className="absolute top-[18%] right-[10%] w-[24%] h-[60%] border-2 border-purple-400 bg-purple-500/10 rounded">
                      <span className="absolute -top-5 left-0 bg-purple-600 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                        Server Rack CISCO [0.94]
                      </span>
                    </div>

                    {/* Box 3: CCTV Camera */}
                    <div className="absolute top-[8%] left-[45%] w-[10%] h-[12%] border-2 border-amber-400 bg-amber-500/10 rounded">
                      <span className="absolute -top-5 left-0 bg-amber-600 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                        CCTV Dome [0.89]
                      </span>
                    </div>

                    {/* Box 4: Sprinkler */}
                    <div className="absolute top-[6%] left-[20%] w-[8%] h-[10%] border-2 border-sky-400 bg-sky-500/10 rounded">
                      <span className="absolute -top-5 left-0 bg-sky-600 text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                        Sprinkler [0.92]
                      </span>
                    </div>
                  </>
                )}

                {/* EXIF Watermark overlay */}
                <div className="absolute bottom-2 left-2 bg-black/75 px-3 py-1 rounded text-[10px] font-mono text-emerald-400">
                  EXIF GPS: 18.5204° N, 73.8567° E · 2026-03-14 11:28:42 IST · Samsung S24 Ultra
                </div>
              </div>

              {/* Room Check Result Box */}
              <div className="mt-5 p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold text-xs text-emerald-950 dark:text-emerald-200">
                    Room Check Diagnostic Assessment
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900">
                    <span className="text-[10px] text-stone-400 uppercase block">Floor Area</span>
                    <strong className="text-emerald-700 dark:text-emerald-300">184 sqm (PASS)</strong>
                  </div>
                  <div className="bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900">
                    <span className="text-[10px] text-stone-400 uppercase block">Terminals</span>
                    <strong className="text-emerald-700 dark:text-emerald-300">68 units (PASS)</strong>
                  </div>
                  <div className="bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900">
                    <span className="text-[10px] text-stone-400 uppercase block">Sprinklers</span>
                    <strong className="text-emerald-700 dark:text-emerald-300">4 heads (PASS)</strong>
                  </div>
                  <div className="bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-900">
                    <span className="text-[10px] text-stone-400 uppercase block">Exit Clearance</span>
                    <strong className="text-emerald-700 dark:text-emerald-300">1.8m width (PASS)</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Metadata Rows (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 block mb-3">
                Photogrammetry EXIF Metadata
              </span>

              <div className="space-y-3 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/60">
                  <span className="text-stone-400 text-[10px] uppercase block font-sans">
                    Timestamp
                  </span>
                  <span className="text-stone-800 dark:text-slate-200">
                    2026-03-14 11:28:42 IST
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/60">
                  <span className="text-stone-400 text-[10px] uppercase block font-sans">
                    GPS Coordinates
                  </span>
                  <span className="text-stone-800 dark:text-slate-200">
                    18.5204° N, 73.8567° E (Plot 42/1A)
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/60">
                  <span className="text-stone-400 text-[10px] uppercase block font-sans">
                    Device Fingerprint
                  </span>
                  <span className="text-stone-800 dark:text-slate-200">
                    Samsung SM-S928B (Hash: a8f9c2...4b12)
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-stone-50 dark:bg-slate-800/60">
                  <span className="text-stone-400 text-[10px] uppercase block font-sans">
                    Cadastral Geofence Verification
                  </span>
                  <span className="text-emerald-600 font-bold font-sans">
                    Inside Campus Boundary (±4.2m error)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ACTIVITY (Audit Trail Table with Chain Intact Banner) */}
      {activeTab === 'ACTIVITY' && (
        <div className="space-y-6">
          {/* Prominent Chain Intact Banner */}
          <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h4 className="font-extrabold text-sm text-emerald-950 dark:text-emerald-200 flex items-center gap-2">
                  Cryptographic Chain Intact
                  <PillBadge variant="verified" size="sm">
                    Merkle Root Verified
                  </PillBadge>
                </h4>
                <p className="text-xs text-emerald-800 dark:text-emerald-300 font-mono mt-0.5">
                  Root: sha256:7f9a2b0ee8172940294819772384910293847192837401928347102e148c7d
                </p>
              </div>
            </div>

            <div className="text-xs text-stone-500 font-sans">
              All 5 ledger transactions verified against sovereign notary anchors.
            </div>
          </div>

          {/* Audit Trail Table */}
          <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl shadow-soft overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-stone-50/80 dark:bg-slate-900/80 border-b border-stone-200 dark:border-slate-800 text-stone-400 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Tx ID & Timestamp</th>
                    <th className="px-4 py-3">Actor / Agent</th>
                    <th className="px-4 py-3">Action Description</th>
                    <th className="px-4 py-3">Cryptographic Hash</th>
                    <th className="px-4 py-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
                  {mockAuditTrail.map((tx) => (
                    <tr
                      key={tx.id}
                      className="hover:bg-stone-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-4 py-3.5">
                        <span className="font-mono font-bold text-stone-900 dark:text-slate-100 block">
                          {tx.id}
                        </span>
                        <span className="text-[11px] text-stone-400 font-mono">{tx.timestamp}</span>
                      </td>
                      <td className="px-4 py-3.5 font-medium text-stone-800 dark:text-slate-200">
                        {tx.actor}
                      </td>
                      <td className="px-4 py-3.5 text-stone-600 dark:text-slate-300">
                        {tx.action}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-[11px] text-purple-700 dark:text-purple-400">
                        {tx.hash}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <PillBadge
                          variant={
                            tx.status === 'Contradicted' || tx.status === 'High Alert'
                              ? 'critical'
                              : 'verified'
                          }
                          size="sm"
                        >
                          {tx.status}
                        </PillBadge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Decide Modal */}
      {isDecideOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 dark:bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-floating border border-stone-200 dark:border-slate-800 p-6 space-y-4">
            <div className="flex items-center gap-2.5 pb-2 border-b border-stone-200 dark:border-slate-800">
              <Gavel className="w-5 h-5 text-purple-600" />
              <h3 className="font-bold text-stone-900 dark:text-white text-base">
                Record Scrutiny Determination
              </h3>
            </div>

            <p className="text-xs text-stone-600 dark:text-slate-400">
              Choose the regulatory determination for{' '}
              <strong className="text-stone-900 dark:text-white">{appData.name}</strong>.
            </p>

            <div className="space-y-2">
              <button
                onClick={() => handleDecisionSubmit('Issue Deficiency Letter')}
                className="w-full p-3 rounded-xl border border-rose-200 bg-rose-50/60 dark:bg-rose-950/30 hover:bg-rose-100 text-left text-xs font-semibold text-rose-900 dark:text-rose-200 transition-colors"
              >
                Issue Deficiency Letter (Mandatory 15-day Rectification)
              </button>

              <button
                onClick={() => handleDecisionSubmit('Recommend Hearing')}
                className="w-full p-3 rounded-xl border border-amber-200 bg-amber-50/60 dark:bg-amber-950/30 hover:bg-amber-100 text-left text-xs font-semibold text-amber-900 dark:text-amber-200 transition-colors"
              >
                Escalate to Standing Hearing Committee (SHC)
              </button>

              <button
                onClick={() => handleDecisionSubmit('Provisional Approval with Conditions')}
                className="w-full p-3 rounded-xl border border-stone-200 bg-stone-50 hover:bg-stone-100 dark:bg-slate-800 dark:border-slate-700 text-left text-xs font-semibold text-stone-700 dark:text-slate-300 transition-colors"
              >
                Grant Conditional Extension of Approval (EoA)
              </button>
            </div>

            {decisionFeedback && (
              <div className="p-3 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-semibold">
                {decisionFeedback}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setIsDecideOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-stone-500 hover:text-stone-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ask Why Drawer */}
      <AskWhyDrawer
        isOpen={isAskWhyOpen}
        onClose={() => setIsAskWhyOpen(false)}
        onNavigateToDocument={(doc, page) => handleShowOnPage(doc, page)}
      />

      {/* Export Evidence Pack Modal */}
      <ExportEvidenceModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        applicationId={appData.id}
        institutionName={appData.name}
      />
    </div>
  );
};
