import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  FileText,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowLeft,
  Send,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { mockApplications, ApplicationItem } from '../../data/mockScrutinyData';
import {
  getDeficienciesForApp,
  respondToDeficiency,
  DeficiencyNotice,
} from '../../data/rectificationStore';

export const InstitutionWorkspacePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();

  const appId = id || 'A1';
  const currentApp: ApplicationItem =
    mockApplications.find(
      (a) =>
        a.id.toLowerCase() === appId.toLowerCase() ||
        a.code?.toLowerCase() === appId.toLowerCase()
    ) || mockApplications[0];

  const [deficiencies, setDeficiencies] = useState<DeficiencyNotice[]>([]);
  const [activeDeficiencyId, setActiveDeficiencyId] = useState<string | null>(null);
  const [responseText, setResponseText] = useState('');
  const [attachedFileName, setAttachedFileName] = useState('');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Supplementary upload
  const [supplementaryCategory, setSupplementaryCategory] = useState('Faculty Register');
  const [supplementaryFile, setSupplementaryFile] = useState('Ratified_Affidavit_2026.pdf');
  const [supplementaryUploaded, setSupplementaryUploaded] = useState(false);

  useEffect(() => {
    const load = () => {
      const items = getDeficienciesForApp(currentApp.id);
      setDeficiencies(items);
      const pending = items.find((i) => i.status === 'PENDING_RESPONSE');
      if (pending) {
        setActiveDeficiencyId(pending.id);
      } else if (items.length > 0) {
        setActiveDeficiencyId(items[0].id);
      }
    };
    load();
    window.addEventListener('nirikshan-deficiencies-changed', load);
    return () => window.removeEventListener('nirikshan-deficiencies-changed', load);
  }, [currentApp.id]);

  const activeDeficiency = deficiencies.find((d) => d.id === activeDeficiencyId);

  const handleSubmitResponse = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDeficiencyId || !responseText.trim()) return;

    respondToDeficiency(
      activeDeficiencyId,
      responseText.trim(),
      attachedFileName || 'Institutional_Compliance_Proof.pdf'
    );

    setSuccessMessage('Rectification response and evidence successfully dispatched to Scrutiny Officer.');
    setResponseText('');
    setAttachedFileName('');
    setTimeout(() => {
      setSuccessMessage(null);
    }, 4000);
  };

  const handleUploadSupplementary = (e: React.FormEvent) => {
    e.preventDefault();
    setSupplementaryUploaded(true);
    setTimeout(() => setSupplementaryUploaded(false), 3500);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Breadcrumb & App Details */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft">
        <div className="flex items-center gap-2 mb-3">
          <Link
            to="/portal"
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>My Applications</span>
          </Link>
          <span className="text-stone-300 dark:text-slate-700">•</span>
          <span className="text-xs text-stone-500 font-mono">
            Workspace: {currentApp.id} ({currentApp.code || 'A1'})
          </span>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-stone-900 dark:text-white">
              {currentApp.name}
            </h1>
            <p className="text-xs text-stone-500 mt-1">
              Location: {currentApp.location} · Directorate: {currentApp.category} · Cycle: 2026–2027
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              Scrutiny In Progress
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
              {currentApp.strongestProof}
            </span>
          </div>
        </div>
      </div>

      {/* Main Workspace Grid: Left Deficiencies list & Right Responder */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Deficiency List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-stone-200 dark:border-slate-800">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-400">
              Officer Deficiency Queries ({deficiencies.length})
            </h2>
          </div>

          <div className="space-y-3">
            {deficiencies.map((d) => (
              <button
                key={d.id}
                onClick={() => setActiveDeficiencyId(d.id)}
                className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer ${
                  activeDeficiencyId === d.id
                    ? 'border-sky-500 bg-sky-50/60 dark:bg-sky-950/40 shadow-xs'
                    : 'border-stone-200 dark:border-slate-800 hover:bg-stone-50 dark:hover:bg-slate-800/60 bg-white dark:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300">
                    {d.ruleClause}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      d.status === 'PENDING_RESPONSE'
                        ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                        : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                    }`}
                  >
                    {d.status === 'PENDING_RESPONSE' ? 'Pending Reply' : 'Submitted'}
                  </span>
                </div>

                <div className="text-xs font-bold text-stone-900 dark:text-white line-clamp-1">
                  {d.subject}
                </div>
                <div className="text-[11px] text-stone-500 mt-1 line-clamp-2">
                  {d.details}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column: Responder & Upload Missing/Corrected Docs */}
        <div className="lg:col-span-7 space-y-6">
          {activeDeficiency ? (
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-7 shadow-soft space-y-5">
              <div className="pb-4 border-b border-stone-200 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-sky-600 dark:text-sky-400">
                    {activeDeficiency.ruleClause}
                  </span>
                  <span className="text-xs text-stone-400">
                    Issued: {activeDeficiency.issuedAt} (Window: {activeDeficiency.deadlineDays} Days)
                  </span>
                </div>
                <h3 className="text-base font-bold text-stone-900 dark:text-white mt-1">
                  {activeDeficiency.subject}
                </h3>
                <p className="text-xs text-stone-600 dark:text-slate-300 mt-2 p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-800/60 leading-relaxed">
                  {activeDeficiency.details}
                </p>
              </div>

              {/* Status Alert if Already Submitted */}
              {activeDeficiency.status === 'SUBMITTED' && (
                <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200 space-y-1.5">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Rectification Response Lodged on {activeDeficiency.respondedAt}</span>
                  </div>
                  <p>{activeDeficiency.institutionResponse}</p>
                  {activeDeficiency.uploadedDoc && (
                    <div className="flex items-center gap-1 font-mono text-[11px] text-emerald-700 dark:text-emerald-300">
                      <FileText className="w-3.5 h-3.5" />
                      <span>Evidence: {activeDeficiency.uploadedDoc}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Response Form */}
              <form onSubmit={handleSubmitResponse} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Institution Rectification Clarification
                  </label>
                  <textarea
                    rows={4}
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    placeholder="Provide specific factual response addressing the officer query, explaining rectified selection committee procedures, renewed NOCs, or statutory compliance..."
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Upload Corrected / Missing Statutory Evidence (PDF)
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={attachedFileName}
                      onChange={(e) => setAttachedFileName(e.target.value)}
                      placeholder="e.g. MFO_Renewed_Fire_NOC_2026.pdf"
                      className="flex-1 text-xs p-2.5 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setAttachedFileName('Ratified_Statutory_Evidence_Document.pdf')}
                      className="px-3.5 py-2.5 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-100 dark:bg-slate-800 text-xs font-semibold hover:bg-stone-200 dark:hover:bg-slate-700 cursor-pointer"
                    >
                      Attach Sample
                    </button>
                  </div>
                </div>

                {successMessage && (
                  <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 text-emerald-800 dark:text-emerald-200 text-xs font-semibold flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span>{successMessage}</span>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white text-xs font-bold flex items-center gap-2 shadow-sm transition-all cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                    <span>Submit Compliance Response</span>
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-8 text-center text-xs text-stone-400">
              Select a deficiency query on the left to review particulars and submit compliance.
            </div>
          )}

          {/* Supplementary Document Uploader Box */}
          <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 shadow-soft space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400 flex items-center gap-1.5">
              <Upload className="w-4 h-4 text-sky-600" />
              <span>Upload Additional Corroborating Statutory Files</span>
            </h3>

            <form onSubmit={handleUploadSupplementary} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 dark:text-slate-400 mb-1">
                    Regulatory Category
                  </label>
                  <select
                    value={supplementaryCategory}
                    onChange={(e) => setSupplementaryCategory(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                  >
                    <option value="Land Title">Land Title & Revenue Record</option>
                    <option value="Building Plan">Approved Building Plan</option>
                    <option value="Fire Safety">Fire Safety Protection NOC</option>
                    <option value="Faculty Register">Faculty EPF & Appointment List</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 dark:text-slate-400 mb-1">
                    PDF Document Filename
                  </label>
                  <input
                    type="text"
                    value={supplementaryFile}
                    onChange={(e) => setSupplementaryFile(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white font-mono"
                    required
                  />
                </div>
              </div>

              {supplementaryUploaded && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 text-emerald-800 dark:text-emerald-200 text-xs font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Document uploaded: SHA-256 hash generated and added to dossier.</span>
                </div>
              )}

              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-stone-100 dark:bg-slate-800 hover:bg-stone-200 dark:hover:bg-slate-700 text-stone-800 dark:text-slate-200 text-xs font-semibold cursor-pointer"
                >
                  Upload & Compute Fingerprint
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
