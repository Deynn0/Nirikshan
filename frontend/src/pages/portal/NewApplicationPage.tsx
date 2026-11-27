import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  CheckCircle2,
  Upload,
  ArrowRight,
  ArrowLeft,
  FileText,
  ShieldCheck,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const NewApplicationPage: React.FC = () => {
  const { session } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form State
  const [instName, setInstName] = useState(
    session?.displayName || 'Apex Institute of Advanced Technology & Research'
  );
  const [program, setProgram] = useState('ENGINEERING_AND_TECHNOLOGY');
  const [level, setLevel] = useState('UNDER_GRADUATE');
  const [intake, setIntake] = useState(240);
  const [locationType, setLocationType] = useState('URBAN');

  // Infrastructure
  const [landArea, setLandArea] = useState('7.5');
  const [builtUpArea, setBuiltUpArea] = useState('14200');
  const [naReference, setNaReference] = useState('REV-SANCTION-2025-NA-8841');
  const [sanctionAuthority, setSanctionAuthority] = useState('Town & Country Planning Directorate');

  // Documents
  const [files, setFiles] = useState<{ [key: string]: string }>({
    landDeed: 'Registered_Sale_Deed_Vol_241.pdf',
    buildingPlan: 'Town_Planning_Sanctioned_Blueprint.pdf',
    fireNoc: 'Municipal_Fire_Protection_NOC_2026.pdf',
    facultyEpf: 'EPFO_ECR_Payroll_March_2026.pdf',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedAppId, setSubmittedAppId] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      const generatedId = `APP-2026-AICTE-${Math.floor(5000 + Math.random() * 4000)}`;
      setSubmittedAppId(generatedId);
      setIsSubmitting(false);
      setStep(4);
    }, 1500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-600 dark:text-sky-400">
            AICTE APH 2026–2027
          </span>
          <span className="text-stone-300 dark:text-slate-700">•</span>
          <span className="text-xs text-stone-500">New Approval Dossier Filing</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 dark:text-white tracking-tight">
          New Institutional & Program Application
        </h1>
        <p className="text-xs text-stone-500 mt-1">
          Submit new program proposal, land infrastructure records, and statutory proof dossiers for Scrutiny Committee review.
        </p>
      </div>

      {/* Progress Steps Header */}
      <div className="grid grid-cols-4 gap-2 text-center text-xs font-semibold pb-4 border-b border-stone-200 dark:border-slate-800">
        <div className={`p-2.5 rounded-xl border transition-all ${step === 1 ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300' : step > 1 ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-stone-200 text-stone-400'}`}>
          1. College & Program
        </div>
        <div className={`p-2.5 rounded-xl border transition-all ${step === 2 ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300' : step > 2 ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-stone-200 text-stone-400'}`}>
          2. Land & Norms
        </div>
        <div className={`p-2.5 rounded-xl border transition-all ${step === 3 ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300' : step > 3 ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-stone-200 text-stone-400'}`}>
          3. Upload Documents
        </div>
        <div className={`p-2.5 rounded-xl border transition-all ${step === 4 ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300' : 'border-stone-200 text-stone-400'}`}>
          4. Review & Submit
        </div>
      </div>

      {/* Wizard Card */}
      <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-soft">
        {/* Step 1 */}
        {step === 1 && (
          <div className="space-y-5">
            <h2 className="text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-sky-600" />
              <span>Institutional & Course Identification</span>
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                  Full Name of Institution
                </label>
                <input
                  type="text"
                  value={instName}
                  onChange={(e) => setInstName(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Program Area
                  </label>
                  <select
                    value={program}
                    onChange={(e) => setProgram(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                  >
                    <option value="ENGINEERING_AND_TECHNOLOGY">Engineering & Technology</option>
                    <option value="MANAGEMENT">Management (MBA / PGDM)</option>
                    <option value="PHARMACY">Pharmacy (B.Pharm / M.Pharm)</option>
                    <option value="POLYTECHNIC">Polytechnic & Diploma</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Academic Level
                  </label>
                  <select
                    value={level}
                    onChange={(e) => setLevel(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                  >
                    <option value="UNDER_GRADUATE">Undergraduate (UG)</option>
                    <option value="POST_GRADUATE">Postgraduate (PG)</option>
                    <option value="DIPLOMA">Diploma</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Proposed Student Intake (Annual Seats)
                  </label>
                  <input
                    type="number"
                    value={intake}
                    onChange={(e) => setIntake(parseInt(e.target.value, 10))}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    min={30}
                    step={30}
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Location Classification
                  </label>
                  <select
                    value={locationType}
                    onChange={(e) => setLocationType(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                  >
                    <option value="URBAN">Urban / Non-Rural (Min 7.5 Acres)</option>
                    <option value="RURAL">Rural (Min 10.0 Acres)</option>
                    <option value="MEGA_CITY">Mega City / NCR (Min 5.0 Acres)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold flex items-center gap-2 cursor-pointer"
              >
                <span>Continue to Land & Norms</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div className="space-y-5">
            <h2 className="text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-sky-600" />
              <span>Campus Land & Infrastructure Dimensions</span>
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Campus Contiguous Land Area (Acres)
                  </label>
                  <input
                    type="text"
                    value={landArea}
                    onChange={(e) => setLandArea(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    required
                  />
                  <span className="text-[11px] text-stone-400 mt-0.5 block">
                    Statutory APH Norm: Minimum 7.5 Acres
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Constructed Built-up Area (Sq. Meters)
                  </label>
                  <input
                    type="text"
                    value={builtUpArea}
                    onChange={(e) => setBuiltUpArea(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    required
                  />
                  <span className="text-[11px] text-stone-400 mt-0.5 block">
                    Instructional, Administrative & Amenities Area
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Non-Agriculture (NA) Sanction Order No.
                  </label>
                  <input
                    type="text"
                    value={naReference}
                    onChange={(e) => setNaReference(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 dark:text-slate-300 mb-1">
                    Building Plan Sanctioning Authority
                  </label>
                  <input
                    type="text"
                    value={sanctionAuthority}
                    onChange={(e) => setSanctionAuthority(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-stone-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-stone-900 dark:text-white"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2.5 rounded-xl border border-stone-200 dark:border-slate-700 text-xs font-semibold text-stone-600 dark:text-slate-300 flex items-center gap-2 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold flex items-center gap-2 cursor-pointer"
              >
                <span>Continue to Document Uploads</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && (
          <div className="space-y-5">
            <h2 className="text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-sky-600" />
              <span>Statutory Document & Certificate Dossier Uploads</span>
            </h2>

            <p className="text-xs text-stone-500">
              Upload digitally signed PDF documents. Each file undergoes deterministic SHA-256 tamper hashing and OCR table extraction.
            </p>

            <div className="space-y-3">
              {[
                {
                  key: 'landDeed',
                  label: 'Registered Land Sale Deed & Ownership Title',
                  clause: 'Clause 1.4',
                },
                {
                  key: 'buildingPlan',
                  label: 'Town Planning Competent Authority Sanctioned Blueprint',
                  clause: 'Clause 3.2',
                },
                {
                  key: 'fireNoc',
                  label: 'Municipal Fire Safety Protection Certificate (NOC)',
                  clause: 'Clause 4.3',
                },
                {
                  key: 'facultyEpf',
                  label: 'Faculty EPF Monthly Challan & Cadre Appointment Census',
                  clause: 'Clause 2.14',
                },
              ].map((doc) => (
                <div
                  key={doc.key}
                  className="p-4 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50/60 dark:bg-slate-850 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-stone-900 dark:text-white">
                        {doc.label}
                      </div>
                      <div className="text-[11px] text-stone-400 font-mono">
                        {doc.clause} · File: {files[doc.key]}
                      </div>
                    </div>
                  </div>

                  <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Attached
                  </span>
                </div>
              ))}
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-4 py-2.5 rounded-xl border border-stone-200 dark:border-slate-700 text-xs font-semibold text-stone-600 dark:text-slate-300 flex items-center gap-2 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-2 shadow-sm cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? (
                  <span>Hashing & Submitting Dossier...</span>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Cryptographically Sign & Lodge Application</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Confirmation */}
        {step === 4 && (
          <div className="text-center py-8 space-y-4">
            <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto shadow-sm">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <h2 className="text-xl font-extrabold text-stone-900 dark:text-white">
              Application Successfully Lodged!
            </h2>

            <p className="text-xs text-stone-600 dark:text-slate-400 max-w-md mx-auto">
              Your application has been received into the AICTE Directorate Air-Gap Scrutiny Pipeline. Deterministic proof hashes and timestamped receipts have been generated.
            </p>

            <div className="p-4 rounded-xl bg-stone-50 dark:bg-slate-800/80 border border-stone-200 dark:border-slate-700 max-w-sm mx-auto font-mono text-xs text-stone-800 dark:text-slate-200">
              <div className="text-[10px] uppercase text-stone-400 font-bold mb-1">Official Reference ID</div>
              <div className="text-base font-extrabold text-sky-600 dark:text-sky-400">
                {submittedAppId}
              </div>
            </div>

            <div className="pt-4 flex items-center justify-center gap-3">
              <button
                onClick={() => navigate('/portal')}
                className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold flex items-center gap-2 cursor-pointer shadow-sm"
              >
                <span>Go to My Applications</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
