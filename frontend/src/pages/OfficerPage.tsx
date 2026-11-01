import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  FileText,
  History,
  Network,
  MapPin,
  HelpCircle,
  AlertTriangle,
  RefreshCw,
  Award,
  Layers,
  CheckCircle2,
  XCircle,
  FileCode,
} from 'lucide-react';
import { useDossiers, useVerifyDossier, useReport } from '../api/hooks';
import { DocumentViewer } from '../components/officer/DocumentViewer';
import { RevisionTimeMachine } from '../components/officer/RevisionTimeMachine';
import { IntegrityNetwork } from '../components/officer/IntegrityNetwork';
import { GeotagMap } from '../components/officer/GeotagMap';
import { AskWhyPanel } from '../components/officer/AskWhyPanel';
import { DeficiencyLetterGenerator } from '../components/officer/DeficiencyLetterGenerator';
import { TrustLadderBadge } from '../components/TrustLadderBadge';

export const OfficerPage: React.FC = () => {
  const { t } = useTranslation();
  const { data: dossiers = [], isLoading, refetch } = useDossiers();
  const verifyDossierMutation = useVerifyDossier();

  const [selectedDossierId, setSelectedDossierId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<
    'VIEWER' | 'REVISIONS' | 'NETWORK' | 'GEOTAG' | 'RULES' | 'ASK_WHY' | 'DEFICIENCY'
  >('VIEWER');

  const currentDossier = dossiers.find((d) => d.dossier_id === selectedDossierId) || dossiers[0];
  const { data: reportData } = useReport(currentDossier?.dossier_id);

  const handleVerify = async () => {
    if (!currentDossier) return;
    try {
      await verifyDossierMutation.mutateAsync(currentDossier.dossier_id);
      refetch();
    } catch (err) {
      console.error('Scrutiny re-evaluation error', err);
    }
  };

  const findings = currentDossier?.findings || [];
  const riskScore = currentDossier?.risk_score || 25.0;
  const overallStatus = currentDossier?.overall_status || 'MANUAL_REVIEW_REQUIRED';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Officer Console Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase tracking-widest text-indigo-400 font-bold">
              AICTE Scrutiny Officer Console
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Deterministic Approval Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <span>{currentDossier?.institution_name || 'Delhi Institute of Advanced Engineering & Tech'}</span>
          </h1>
          <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-400 font-mono">
            <span>Dossier: <span className="text-sky-300">{currentDossier?.dossier_id || 'dos-sample'}</span></span>
            <span>•</span>
            <span>Ref: <span className="text-slate-200">{currentDossier?.application_number || 'AICTE-2026-DEL-001'}</span></span>
            <span>•</span>
            <span>Program: <span className="text-slate-200">{currentDossier?.program || 'Engineering & Tech'}</span></span>
          </div>
        </div>

        {/* Action & Status Cards */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Dossier Selector */}
          {dossiers.length > 0 && (
            <select
              value={currentDossier?.dossier_id || ''}
              onChange={(e) => setSelectedDossierId(e.target.value)}
              className="px-3 py-2 rounded-xl glass-input text-xs text-white max-w-[200px] truncate"
            >
              {dossiers.map((d) => (
                <option key={d.dossier_id} value={d.dossier_id} className="bg-slate-900 text-white">
                  {d.institution_name}
                </option>
              ))}
            </select>
          )}

          {/* Re-verify engine button */}
          <button
            type="button"
            onClick={handleVerify}
            disabled={verifyDossierMutation.isPending}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifyDossierMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Re-Verify Rules</span>
          </button>

          {/* Status Badge */}
          <div
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold tracking-wide flex items-center gap-1.5 ${
              overallStatus === 'PASS'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : overallStatus === 'FLAGGED_TAMPER'
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
            }`}
          >
            {overallStatus === 'PASS' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            )}
            <span>{overallStatus}</span>
          </div>

          {/* Risk Score */}
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-right">
            <div className="text-[10px] text-slate-400 font-mono">Risk Index</div>
            <div
              className={`text-sm font-black font-mono ${
                riskScore > 60 ? 'text-rose-400' : riskScore > 30 ? 'text-amber-400' : 'text-emerald-400'
              }`}
            >
              {riskScore.toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          type="button"
          onClick={() => setActiveTab('VIEWER')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'VIEWER'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileText className="w-4 h-4 text-indigo-400" />
          <span>Document Viewer (pdf.js)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('REVISIONS')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'REVISIONS'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <History className="w-4 h-4 text-purple-400" />
          <span>Revision Time Machine</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('NETWORK')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'NETWORK'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Network className="w-4 h-4 text-rose-400" />
          <span>Integrity Network</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('GEOTAG')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'GEOTAG'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <MapPin className="w-4 h-4 text-sky-400" />
          <span>Geotag Map</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('RULES')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'RULES'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Award className="w-4 h-4 text-emerald-400" />
          <span>Trust Ladder & Findings</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300">
            {findings.length || 3}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('ASK_WHY')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'ASK_WHY'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <HelpCircle className="w-4 h-4 text-amber-400" />
          <span>"Ask Why" Assistant</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('DEFICIENCY')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'DEFICIENCY'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileCode className="w-4 h-4 text-orange-400" />
          <span>Deficiency Letter Generator</span>
        </button>
      </div>

      {/* Tab 1: Document Viewer */}
      {activeTab === 'VIEWER' && (
        <DocumentViewer
          dossierId={currentDossier?.dossier_id || 'dos-demo'}
          documentId={currentDossier?.documents?.[0]?.document_id || 'doc-land-01'}
          documentTitle={currentDossier?.documents?.[0]?.title || 'Registered Land Sale Deed (Vol-3)'}
          pageCount={currentDossier?.documents?.[0]?.page_count || 3}
          findings={findings}
        />
      )}

      {/* Tab 2: Revision Time Machine */}
      {activeTab === 'REVISIONS' && <RevisionTimeMachine />}

      {/* Tab 3: Integrity Network */}
      {activeTab === 'NETWORK' && <IntegrityNetwork />}

      {/* Tab 4: Geotag Map */}
      {activeTab === 'GEOTAG' && <GeotagMap />}

      {/* Tab 5: Trust Ladder & Rule Findings */}
      {activeTab === 'RULES' && (
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Evidence Trust Ladder & Rule Verification Matrix
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-sky-300 font-mono">
                  APH 2024-2027
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Every evidence item is tagged with its cryptographic or statutory trust level. Models are strictly labeled "Advisory".
              </p>
            </div>

            {/* Trust Ladder Distribution */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <TrustLadderBadge level="CRYPTOGRAPHIC_PROOF" size="sm" />
              <TrustLadderBadge level="STATUTORY_DATABASE" size="sm" />
              <TrustLadderBadge level="HARDENED_DOCUMENT" size="sm" />
              <TrustLadderBadge level="MODEL_PREDICTION" size="sm" isModelAdvisory />
              <TrustLadderBadge level="UNVERIFIED_CLAIM" size="sm" />
            </div>
          </div>

          {/* Finding Cards */}
          <div className="space-y-4">
            {(findings.length > 0 ? findings : [
              {
                finding_id: 'f-1',
                rule_id: 'AICTE-2024-LAND-001',
                rule_name: 'Minimum Campus Land Area',
                category: 'Infrastructure',
                status: 'PASS',
                summary: 'Contiguous land parcel of 5.50 acres verified in rural category.',
                details: 'Satisfies AICTE 2024-2027 statutory minimum threshold of 5.0 acres for technical campus establishment.',
                handbook_citation: { clause_number: 'Clause 7.1', handbook_edition: 'APH 2024-2027' },
                evidence_list: [
                  { label: 'Sub-Registrar Digital Seal', trust_level: 'CRYPTOGRAPHIC_PROOF' },
                  { label: 'Revenue Department Land Registry', trust_level: 'STATUTORY_DATABASE' },
                ],
                is_model_advisory_only: false,
                needs_verification: false,
              },
              {
                finding_id: 'f-2',
                rule_id: 'AICTE-2024-CADRE-001',
                rule_name: 'Academic Staff Cadre Ratio (1:2:6)',
                category: 'Faculty',
                status: 'FAIL',
                summary: 'Missing regular full-time Professor in Department of Computer Science.',
                details: 'Current declared faculty comprises 0 Professors, 4 Associate Professors, and 14 Assistant Professors. AICTE norms mandate at least 1 regular Professor.',
                handbook_citation: { clause_number: 'Appendix 7.2', handbook_edition: 'APH 2024-2027' },
                evidence_list: [
                  { label: 'YOLOX Lab Asset Counter', trust_level: 'MODEL_PREDICTION' },
                  { label: 'Applicant Faculty Affidavit', trust_level: 'UNVERIFIED_CLAIM' },
                ],
                is_model_advisory_only: true,
                needs_verification: true,
              },
              {
                finding_id: 'f-3',
                rule_id: 'AICTE-2024-FIRE-001',
                rule_name: 'Fire Department Safety Clearance NOC',
                category: 'Safety',
                status: 'MANUAL_REVIEW_REQUIRED',
                summary: 'Fire Safety Certificate expired; renewal application under verification.',
                details: 'State fire authority inspection completed; active validity certificate pending final committee review.',
                handbook_citation: { clause_number: 'Clause 5.3', handbook_edition: 'APH 2024-2027' },
                evidence_list: [
                  { label: 'State Fire Service Receipt', trust_level: 'HARDENED_DOCUMENT' },
                ],
                is_model_advisory_only: false,
                needs_verification: true,
              },
            ]).map((item: any) => {
              const isPass = item.status === 'PASS';
              const isFail = item.status === 'FAIL';

              return (
                <div
                  key={item.finding_id}
                  className={`p-4 rounded-xl border space-y-3 ${
                    isPass
                      ? 'bg-slate-900/60 border-emerald-500/30'
                      : isFail
                      ? 'bg-rose-950/20 border-rose-500/40'
                      : 'bg-amber-950/20 border-amber-500/40'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-sm text-white">{item.rule_name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {item.rule_id}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-500/30">
                          {item.category}
                        </span>
                      </div>
                      <div className="text-xs text-sky-400 font-mono mt-1">
                        Clause Citation: {item.handbook_citation?.clause_number} ({item.handbook_citation?.handbook_edition})
                      </div>
                    </div>

                    <span
                      className={`inline-block px-2.5 py-1 rounded text-xs font-bold tracking-wide ${
                        isPass
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : isFail
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{item.details || item.summary}</p>

                  {/* Evidence Items with Trust Ladder Badges */}
                  <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-3">
                    <span className="text-[11px] font-semibold text-slate-400">Supporting Evidence:</span>
                    {item.evidence_list && item.evidence_list.map((ev: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-1.5">
                        <span className="text-xs text-slate-300">{ev.label || ev.description}:</span>
                        <TrustLadderBadge
                          level={ev.trust_level || ev.trustLevel}
                          size="sm"
                          isModelAdvisory={item.is_model_advisory_only}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 6: Ask Why Assistant */}
      {activeTab === 'ASK_WHY' && <AskWhyPanel findings={findings} />}

      {/* Tab 7: Deficiency Letter Generator */}
      {activeTab === 'DEFICIENCY' && (
        <DeficiencyLetterGenerator
          institutionName={currentDossier?.institution_name}
          applicationNumber={currentDossier?.application_number}
          findings={findings}
        />
      )}
    </div>
  );
};
