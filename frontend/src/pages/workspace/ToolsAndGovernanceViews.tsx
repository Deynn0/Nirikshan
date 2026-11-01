import React, { useState } from 'react';
import {
  FileText,
  Upload,
  ShieldCheck,
  Network,
  Cpu,
  BookOpen,
  History,
  Server,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Search,
  Sliders,
  Database,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { PillBadge } from '../../components/common/PillBadge';
import { mockFindings, mockAuditTrail } from '../../data/mockScrutinyData';

// 1. Analyse a Document View
export const AnalyseDocumentView: React.FC = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const handleStartAnalysis = (filename: string) => {
    setSelectedFile(filename);
    setAnalyzing(true);
    setAnalyzed(false);
    setTimeout(() => {
      setAnalyzing(false);
      setAnalyzed(true);
    }, 1800);
  };

  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Tools · Document Forensics
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Analyse a Document
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Upload certificates, land deeds, or statutory rosters for instant PDF stream forensic parsing, OCR glyph verification, and trust ladder assignment.
        </p>
      </div>

      {/* Drag and Drop Zone */}
      <div className="surface-card bg-white dark:bg-slate-900 border-2 border-dashed border-stone-300 dark:border-slate-700 rounded-2xl p-10 text-center hover:border-purple-500 transition-colors cursor-pointer">
        <div className="w-14 h-14 rounded-2xl bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 flex items-center justify-center mx-auto mb-4">
          <Upload className="w-7 h-7" />
        </div>
        <h3 className="font-bold text-base text-stone-900 dark:text-white">
          Drop PDF Document Here for Forensics
        </h3>
        <p className="text-xs text-stone-500 max-w-md mx-auto mt-1">
          Supports scanned land deeds, architect carpet area certificates, and digitally signed PDF portfolios up to 50 MB.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => handleStartAnalysis('Architect_Builtup_Area_Certificate.pdf')}
            className="px-4 py-2 rounded-xl bg-purple-50 dark:bg-purple-950/40 hover:bg-purple-100 text-purple-700 dark:text-purple-300 text-xs font-semibold border border-purple-200 dark:border-purple-800"
          >
            Load Sample: Architect_Builtup_Certificate.pdf
          </button>
          <button
            onClick={() => handleStartAnalysis('SubRegistrar_Lease_Deed_Pune.pdf')}
            className="px-4 py-2 rounded-xl bg-stone-100 dark:bg-slate-800 hover:bg-stone-200 text-stone-700 dark:text-slate-300 text-xs font-semibold"
          >
            Load Sample: SubRegistrar_Lease_Deed.pdf
          </button>
        </div>
      </div>

      {/* Analysis Progress */}
      {analyzing && (
        <div className="surface-card bg-white dark:bg-slate-900 border border-purple-200 dark:border-purple-800 rounded-xl p-6 text-center space-y-3">
          <RotateCw className="w-8 h-8 text-purple-600 animate-spin mx-auto" />
          <h4 className="font-bold text-sm text-stone-900 dark:text-white">
            Running 4-Tier Forensic Pipeline on {selectedFile}...
          </h4>
          <p className="text-xs text-stone-500">
            Parsing PDF xref tables → Checking digital signature timestamps → Evaluating OCR font stream glyph substitution
          </p>
        </div>
      )}

      {/* Analysis Results */}
      {analyzed && (
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-6 shadow-soft space-y-5 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800">
            <div>
              <span className="font-mono text-xs font-bold text-stone-900 dark:text-white">
                {selectedFile}
              </span>
              <p className="text-[11px] text-stone-400 font-mono">
                SHA-256: 4d83e2f1839a829104ebc7612c77d9401bf5199859f14ba6
              </p>
            </div>
            <PillBadge variant="critical">Forensic Alert Triggered</PillBadge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900">
              <span className="text-[10px] uppercase font-bold text-rose-700 dark:text-rose-400 block">
                PDF Stream Integrity
              </span>
              <strong className="text-rose-900 dark:text-rose-200 text-sm">
                MODIFIED POST-SIGN
              </strong>
              <p className="text-[11px] text-rose-700 dark:text-rose-300 mt-1">
                Incremental append detected at byte 0x004F8A20.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900">
              <span className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-400 block">
                Digital Signature
              </span>
              <strong className="text-emerald-900 dark:text-emerald-200 text-sm">
                PKCS#7 VALID
              </strong>
              <p className="text-[11px] text-emerald-700 dark:text-emerald-300 mt-1">
                Issued by eMudhra CA for Architect R. K. Joshi.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900">
              <span className="text-[10px] uppercase font-bold text-purple-700 dark:text-purple-400 block">
                Trust Ladder Level
              </span>
              <strong className="text-purple-900 dark:text-purple-200 text-sm">
                E4 (Downgraded to E1)
              </strong>
              <p className="text-[11px] text-purple-700 dark:text-purple-300 mt-1">
                Tampered layer invalidates cryptographic weight.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// 2. Integrity View
export const IntegrityView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Tools · Cross-Institutional Collusion Detector
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Integrity & Network Graph
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Detect shell institutions, shared trustee syndicates, and duplicate ghost faculty shared across multiple regional directorates.
        </p>
      </div>

      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-6 shadow-soft space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800">
          <div>
            <h4 className="font-bold text-sm text-stone-900 dark:text-white">
              Syndicate Detection Cluster: Vidya Vikas Trust (WRO-MH-09)
            </h4>
            <p className="text-xs text-stone-500">
              Connected across 4 sister colleges with 7 overlapping trustee directors and 3 shared faculty
            </p>
          </div>
          <PillBadge variant="critical">Critical Risk</PillBadge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50 dark:bg-slate-800/40 space-y-2 text-xs">
            <span className="font-bold text-stone-900 dark:text-white block">
              Flagged Ghost Faculty Cluster
            </span>
            <ul className="space-y-1.5 text-stone-600 dark:text-slate-300">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span>Dr. V. R. Patil — Listed at Apex Pune & Apex Solapur concurrently</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span>Prof. S. N. Kulkarni — Matched identical EPF account in Nashik</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>Dr. M. G. Joshi — Research guide credentials shared across 3 polytechnics</span>
              </li>
            </ul>
          </div>

          <div className="p-4 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50 dark:bg-slate-800/40 space-y-2 text-xs">
            <span className="font-bold text-stone-900 dark:text-white block">
              Registered Address Collusion
            </span>
            <p className="text-stone-600 dark:text-slate-300">
              Survey Plot 42/1A is declared simultaneously by both Apex Institute of Technology and Trinity Polytechnic Institute, leading to double-counting of required 9.61 contiguous acres.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// 3. Issuer Simulator View
export const IssuerSimulatorView: React.FC = () => {
  const [simState, setSimState] = useState<'IDLE' | 'SIMULATING' | 'SUCCESS'>('IDLE');

  const runSimulation = () => {
    setSimState('SIMULATING');
    setTimeout(() => {
      setSimState('SUCCESS');
    }, 1200);
  };

  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Tools · Statutory Registry Emulation
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Issuer Simulator
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Simulate statutory issuer APIs: AICTE Central Portal, State Land Cadastre, University Convocation Roll, and Digilocker PSS Notary.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-xs text-stone-900 dark:text-white">AICTE Central Registry</h4>
            <PillBadge variant="verified" size="sm">Online</PillBadge>
          </div>
          <p className="text-[11px] text-stone-500">
            Mocks prior-year Extension of Approval (EoA) and sanctioned intake records.
          </p>
          <button
            onClick={runSimulation}
            className="w-full py-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold"
          >
            Simulate Response
          </button>
        </div>

        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-xs text-stone-900 dark:text-white">State Land Cadastre (GIS)</h4>
            <PillBadge variant="verified" size="sm">Online</PillBadge>
          </div>
          <p className="text-[11px] text-stone-500">
            Mocks revenue 7/12 extract parcel polygon coordinates and registered encumbrances.
          </p>
          <button
            onClick={runSimulation}
            className="w-full py-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold"
          >
            Simulate Response
          </button>
        </div>

        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-xs text-stone-900 dark:text-white">Digilocker PSS Anchor</h4>
            <PillBadge variant="verified" size="sm">Online</PillBadge>
          </div>
          <p className="text-[11px] text-stone-500">
            Mocks cryptographic timestamp attestations and e-Aadhaar biometric digests.
          </p>
          <button
            onClick={runSimulation}
            className="w-full py-2 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] text-white text-xs font-semibold"
          >
            Trigger Emulation
          </button>
        </div>
      </div>

      {simState === 'SUCCESS' && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 text-xs text-emerald-800 dark:text-emerald-300">
          Simulation verified: 3 simulated responses returned with cryptographic mock headers.
        </div>
      )}
    </div>
  );
};

// 4. Rules View
export const RulesView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Governance · Statutory Knowledge Base
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Scrutiny Rules Catalog
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Active AICTE Approval Process Handbook (APH 2026–27) rules, algorithmic thresholds, and severity penalty weights.
        </p>
      </div>

      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl shadow-soft overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-stone-50 dark:bg-slate-800/80 text-[10px] uppercase font-semibold text-stone-400 border-b border-stone-200 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">Rule ID</th>
              <th className="px-4 py-3">Title & Statute</th>
              <th className="px-4 py-3">Threshold / Formula</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
            <tr>
              <td className="px-4 py-3 font-mono font-bold text-purple-700">RULE-LND-02</td>
              <td className="px-4 py-3">
                <span className="font-semibold text-stone-900 dark:text-white block">
                  Minimum 30-Year Registered Land Lease
                </span>
                <span className="text-[11px] text-stone-500">AICTE APH Appendix 4, Cl 4.1.2</span>
              </td>
              <td className="px-4 py-3 font-mono text-[11px]">
                lease_remaining_years &gt;= 30.0
              </td>
              <td className="px-4 py-3"><PillBadge variant="critical">Critical</PillBadge></td>
              <td className="px-4 py-3 text-right text-emerald-600 font-semibold">Active</td>
            </tr>
            <tr>
              <td className="px-4 py-3 font-mono font-bold text-purple-700">RULE-FAC-15</td>
              <td className="px-4 py-3">
                <span className="font-semibold text-stone-900 dark:text-white block">
                  Cross-Institution Faculty Deduplication
                </span>
                <span className="text-[11px] text-stone-500">Gazette Anti-Ghost Faculty Norm</span>
              </td>
              <td className="px-4 py-3 font-mono text-[11px]">
                duplicate_aadhaar_hash_count == 0
              </td>
              <td className="px-4 py-3"><PillBadge variant="critical">Critical</PillBadge></td>
              <td className="px-4 py-3 text-right text-emerald-600 font-semibold">Active</td>
            </tr>
            <tr>
              <td className="px-4 py-3 font-mono font-bold text-purple-700">RULE-SEC-04</td>
              <td className="px-4 py-3">
                <span className="font-semibold text-stone-900 dark:text-white block">
                  PDF Incremental Stream Alteration Detection
                </span>
                <span className="text-[11px] text-stone-500">IT Act 2000 Section 65B Forensics</span>
              </td>
              <td className="px-4 py-3 font-mono text-[11px]">
                xref_append_post_signature == False
              </td>
              <td className="px-4 py-3"><PillBadge variant="critical">Critical</PillBadge></td>
              <td className="px-4 py-3 text-right text-emerald-600 font-semibold">Active</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

// 5. Audit Log View
export const AuditLogView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Governance · Immutable Ledger
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Global Scrutiny Audit Log
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Cryptographically notarized transactions, Merkle leaf commitments, and regulatory officer annotations.
        </p>
      </div>

      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl shadow-soft overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-stone-50 dark:bg-slate-800/80 text-[10px] uppercase font-semibold text-stone-400 border-b border-stone-200 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3">Tx Hash & Time</th>
              <th className="px-4 py-3">Actor</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3 text-right">Integrity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
            {mockAuditTrail.map((tx) => (
              <tr key={tx.id} className="hover:bg-stone-50 dark:hover:bg-slate-800/40">
                <td className="px-4 py-3.5">
                  <span className="font-mono font-bold text-stone-900 dark:text-white block">
                    {tx.id}
                  </span>
                  <span className="text-[11px] text-stone-400 font-mono">{tx.timestamp}</span>
                </td>
                <td className="px-4 py-3.5 font-medium">{tx.actor}</td>
                <td className="px-4 py-3.5 text-stone-600 dark:text-slate-300">{tx.action}</td>
                <td className="px-4 py-3.5 text-right">
                  <PillBadge variant="verified" size="sm">Sealed</PillBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// 6. Platform View
export const PlatformView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
          Governance · System Telemetry
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white mt-0.5">
          Platform Architecture & Health
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Cryptographic trust anchors, OCR microservice latency, and sovereign registry connector status.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
          <span className="text-[10px] uppercase font-bold text-stone-400 block">Trust Root</span>
          <strong className="text-base text-stone-900 dark:text-white">AICTE Notary Node #01</strong>
          <p className="text-xs text-emerald-600 font-semibold mt-1">Online · Merkle Height 1,482</p>
        </div>

        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
          <span className="text-[10px] uppercase font-bold text-stone-400 block">OCR Engine</span>
          <strong className="text-base text-stone-900 dark:text-white">Tesseract + LayoutLMv3</strong>
          <p className="text-xs text-stone-500 mt-1">Avg latency: 480ms / page</p>
        </div>

        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft">
          <span className="text-[10px] uppercase font-bold text-stone-400 block">Sovereign Connectors</span>
          <strong className="text-base text-stone-900 dark:text-white">Digilocker & AISHE</strong>
          <p className="text-xs text-emerald-600 font-semibold mt-1">100% Uptime (Last 30d)</p>
        </div>
      </div>
    </div>
  );
};
