import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  FilePlus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Calendar,
  MapPin,
  Send,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { mockApplications, ApplicationItem } from '../../data/mockScrutinyData';
import { getDeficienciesForApp, DeficiencyNotice } from '../../data/rectificationStore';
import { PillBadge } from '../../components/common/PillBadge';

export const MyApplicationsPage: React.FC = () => {
  const { session } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const username = session?.username || 'inst1';
  // Match application corresponding to inst1..inst11
  const userAppIndex = username.toLowerCase().startsWith('inst')
    ? parseInt(username.slice(4), 10)
    : 1;

  const validIndex = isNaN(userAppIndex) || userAppIndex < 1 || userAppIndex > 11 ? 1 : userAppIndex;
  const targetCode = `A${validIndex}`;

  const currentApp: ApplicationItem =
    mockApplications.find(
      (a) =>
        a.instUser === username.toLowerCase() ||
        a.code === targetCode
    ) || mockApplications[0];

  const [deficiencies, setDeficiencies] = useState<DeficiencyNotice[]>([]);

  useEffect(() => {
    const load = () => {
      setDeficiencies(getDeficienciesForApp(currentApp.id));
    };
    load();
    window.addEventListener('nirikshan-deficiencies-changed', load);
    return () => window.removeEventListener('nirikshan-deficiencies-changed', load);
  }, [currentApp.id]);

  const pendingDeficiencies = deficiencies.filter((d) => d.status === 'PENDING_RESPONSE');

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* 1. Header with Institution Overview & New Application CTA */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
              Application {currentApp.code || targetCode}
            </span>
            <span className="text-stone-300 dark:text-slate-700">•</span>
            <span className="text-xs text-stone-500 font-medium">AICTE Cycle 2026–2027</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 dark:text-white tracking-tight">
            {currentApp.name}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs text-stone-500 mt-2 font-sans">
            <span className="font-mono bg-stone-100 dark:bg-slate-800 px-2.5 py-1 rounded-md text-stone-700 dark:text-slate-300 font-semibold">
              {currentApp.id}
            </span>
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-stone-400" />
              {currentApp.location}
            </span>
            <span className="flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-stone-400" />
              {currentApp.category} Program
            </span>
            <span className="flex items-center gap-1.5 font-mono">
              <Calendar className="w-3.5 h-3.5 text-stone-400" />
              Lodged: {currentApp.submittedAt}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/portal/new"
            className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white text-xs font-bold flex items-center gap-2 shadow-sm transition-all"
          >
            <FilePlus className="w-4 h-4" />
            <span>Submit New Application</span>
          </Link>
        </div>
      </div>

      {/* 2. Approval Progress Tracker (Stepper) */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft">
        <h2 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-6">
          Statutory Scrutiny & Approval Progress
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {/* Step 1 */}
          <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-800/80 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold text-emerald-700 dark:text-emerald-400">
                STAGE 01
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-xs font-bold text-stone-900 dark:text-white">
              Application Ingestion
            </p>
            <p className="text-[11px] text-stone-500">
              Statutory documents cryptographic hashing completed.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-800/80 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold text-emerald-700 dark:text-emerald-400">
                STAGE 02
              </span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-xs font-bold text-stone-900 dark:text-white">
              Automated OCR & Rules Check
            </p>
            <p className="text-[11px] text-stone-500">
              APH norm validation completed across 5 statutory clauses.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-800/80 bg-amber-50/60 dark:bg-amber-950/20 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold text-amber-700 dark:text-amber-400">
                STAGE 03
              </span>
              <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400 animate-pulse" />
            </div>
            <p className="text-xs font-bold text-stone-900 dark:text-white">
              Officer Scrutiny & Verification
            </p>
            <p className="text-[11px] text-stone-500">
              Active deficiency rectification review underway.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-4 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50 dark:bg-slate-800/50 space-y-1.5 opacity-75">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold text-stone-400">
                STAGE 04
              </span>
              <ShieldCheck className="w-4 h-4 text-stone-400" />
            </div>
            <p className="text-xs font-bold text-stone-700 dark:text-slate-300">
              Board Final EoA Outcome
            </p>
            <p className="text-[11px] text-stone-400">
              Determination pending completion of stage 3.
            </p>
          </div>
        </div>
      </div>

      {/* 3. Active Deficiencies & Officer Rectification Letters */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-200 dark:border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span>Active Deficiencies & Rectification Notices</span>
              {pendingDeficiencies.length > 0 && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                  {pendingDeficiencies.length} Action Required
                </span>
              )}
            </h2>
            <p className="text-xs text-stone-500 mt-1">
              Statutory inquiries issued by AICTE Scrutiny Officers. Failure to rectify within 15 days may lead to EoA rejection.
            </p>
          </div>

          <Link
            to={`/portal/applications/${currentApp.code || targetCode}`}
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
          >
            <span>Open Application Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {deficiencies.length === 0 ? (
          <div className="text-center py-8 text-stone-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            No active deficiencies recorded for this institution.
          </div>
        ) : (
          <div className="space-y-4">
            {deficiencies.map((d) => (
              <div
                key={d.id}
                className="p-5 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50/50 dark:bg-slate-850 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300">
                      {d.ruleClause}
                    </span>
                    <span className="text-xs font-bold text-stone-900 dark:text-white">
                      {d.subject}
                    </span>
                  </div>

                  <span
                    className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${
                      d.status === 'PENDING_RESPONSE'
                        ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                        : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                    }`}
                  >
                    {d.status === 'PENDING_RESPONSE'
                      ? 'Action Required (15-Day Window)'
                      : 'Rectification Response Lodged'}
                  </span>
                </div>

                <p className="text-xs text-stone-600 dark:text-slate-300 leading-relaxed">
                  {d.details}
                </p>

                {d.institutionResponse && (
                  <div className="p-3 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200">
                    <div className="font-semibold text-[11px] uppercase tracking-wide mb-1 text-emerald-700 dark:text-emerald-400">
                      Your Lodged Rectification Response ({d.respondedAt}):
                    </div>
                    <p>{d.institutionResponse}</p>
                    {d.uploadedDoc && (
                      <div className="mt-1.5 flex items-center gap-1.5 font-mono text-[11px] text-emerald-600 dark:text-emerald-300">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Attached Evidence: {d.uploadedDoc}</span>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-stone-200 dark:border-slate-800 text-[11px] text-stone-400">
                  <span>Issued Date: {d.issuedAt} · Mandatory Window: {d.deadlineDays} Days</span>
                  <Link
                    to={`/portal/applications/${currentApp.code || targetCode}`}
                    className="font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
                  >
                    {d.status === 'PENDING_RESPONSE' ? 'Respond & Upload Evidence' : 'View in Workspace'}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Statutory Uploaded Dossiers & Proof Strength */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft">
        <h2 className="text-base font-bold text-stone-900 dark:text-white mb-4">
          Statutory Document Registry & Cryptographic Fingerprints
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-stone-200 dark:border-slate-800 text-[11px] uppercase font-bold text-stone-400">
                <th className="py-2.5">Document Requirement</th>
                <th className="py-2.5">Statutory Standard</th>
                <th className="py-2.5">Cryptographic Level</th>
                <th className="py-2.5 text-right">Verification Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 dark:divide-slate-800/60">
              <tr>
                <td className="py-3 font-semibold text-stone-900 dark:text-white">
                  Land Ownership & NA Sanction Order
                </td>
                <td className="py-3 text-stone-500">APH 2026 Table 1.1 (Min 7.5 Acres)</td>
                <td className="py-3">
                  <span className="font-mono text-purple-700 dark:text-purple-300 font-bold">
                    E4 Digilocker
                  </span>
                </td>
                <td className="py-3 text-right">
                  <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-[10px]">
                    Verified Clean
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 font-semibold text-stone-900 dark:text-white">
                  Municipal Fire Safety Certificate NOC
                </td>
                <td className="py-3 text-stone-500">NBC Part IV Fire Protection</td>
                <td className="py-3">
                  <span className="font-mono text-purple-700 dark:text-purple-300 font-bold">
                    E3 Statutory OCR
                  </span>
                </td>
                <td className="py-3 text-right">
                  <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-[10px]">
                    Deficiency Notice Issued
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 font-semibold text-stone-900 dark:text-white">
                  Faculty EPF Electronic Challan Receipt (ECR)
                </td>
                <td className="py-3 text-stone-500">Cadre Ratio 1:2:6 & 1:15 Norm</td>
                <td className="py-3">
                  <span className="font-mono text-purple-700 dark:text-purple-300 font-bold">
                    E5 Cryptographic PSS
                  </span>
                </td>
                <td className="py-3 text-right">
                  <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold text-[10px]">
                    Under Scrutiny
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
