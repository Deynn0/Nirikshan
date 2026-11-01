import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Building2, Plus, RefreshCw, FileText, CheckCircle2, AlertTriangle, ShieldCheck, Clock, Layers } from 'lucide-react';
import { useDossiers, useCreateDossier, useVerifyDossier } from '../api/hooks';
import { DocumentUploader } from '../components/applicant/DocumentUploader';
import { LiveJobProgress } from '../components/applicant/LiveJobProgress';
import { SelfAssessmentChecker } from '../components/applicant/SelfAssessmentChecker';
import { RectificationThread } from '../components/applicant/RectificationThread';
import { TrustLadderBadge } from '../components/TrustLadderBadge';

export const ApplicantPage: React.FC = () => {
  const { t } = useTranslation();
  const { data: dossiers = [], isLoading, refetch } = useDossiers();
  const createDossierMutation = useCreateDossier();
  const verifyDossierMutation = useVerifyDossier();

  const [selectedDossierId, setSelectedDossierId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'SELF_CHECK' | 'UPLOAD_DOCS' | 'RECTIFICATION'>('SELF_CHECK');
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Modal for new dossier
  const [showNewModal, setShowNewModal] = useState(false);
  const [newInstName, setNewInstName] = useState('Delhi Institute of Advanced Engineering & Tech');
  const [newAppNo, setNewAppNo] = useState(`AICTE-2026-${Math.floor(1000 + Math.random() * 9000)}`);
  const [newProgram, setNewProgram] = useState('ENGINEERING_AND_TECHNOLOGY');
  const [newLevel, setNewLevel] = useState('UNDER_GRADUATE');
  const [newLocation, setNewLocation] = useState('RURAL');
  const [newIntake, setNewIntake] = useState(240);

  // Set default selected dossier once loaded
  const currentDossier = dossiers.find((d) => d.dossier_id === selectedDossierId) || dossiers[0];

  const handleCreateDossier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createDossierMutation.mutateAsync({
        institution_name: newInstName,
        application_number: newAppNo,
        program: newProgram,
        level: newLevel,
        institution_type: 'PRIVATE_SELF_FINANCED',
        location_type: newLocation,
        intake_proposed: newIntake,
      });
      setSelectedDossierId(created.dossier_id);
      setShowNewModal(false);
      refetch();
    } catch (err) {
      console.error('Failed to create dossier', err);
    }
  };

  const handleRunVerify = async () => {
    if (!currentDossier) return;
    try {
      await verifyDossierMutation.mutateAsync(currentDossier.dossier_id);
      refetch();
    } catch (err) {
      console.error('Verify failed', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title & Institution Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase tracking-widest text-sky-400 font-bold">
              AICTE Applicant Portal
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Institutional Filing Console</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>{currentDossier?.institution_name || 'Institution Compliance Dossier'}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Application Ref: <span className="text-sky-300 font-semibold">{currentDossier?.application_number || 'AICTE-2026-APP-001'}</span>
            {' | '} Program: <span className="text-slate-200">{currentDossier?.program || 'Engineering & Tech'}</span>
            {' | '} Proposed Intake: <span className="text-slate-200">{currentDossier?.intake_proposed || 240} Seats</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Dossier dropdown selector */}
          {dossiers.length > 0 && (
            <select
              value={currentDossier?.dossier_id || ''}
              onChange={(e) => setSelectedDossierId(e.target.value)}
              className="px-3 py-2 rounded-xl glass-input text-xs text-white max-w-[220px] truncate"
            >
              {dossiers.map((d) => (
                <option key={d.dossier_id} value={d.dossier_id} className="bg-slate-900 text-white">
                  {d.institution_name} ({d.application_number})
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={() => setShowNewModal(true)}
            className="px-3 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-sky-600/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Dossier</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          type="button"
          onClick={() => setActiveTab('SELF_CHECK')}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'SELF_CHECK'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <ShieldCheck className="w-4 h-4 text-sky-400" />
          <span>Pre-Submission Self-Assessment</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('UPLOAD_DOCS')}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'UPLOAD_DOCS'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileText className="w-4 h-4 text-sky-400" />
          <span>Upload Documents & Live Pipeline</span>
          {currentDossier?.documents && (
            <span className="px-1.5 py-0.5 rounded-full bg-slate-800 text-[10px] text-sky-300">
              {currentDossier.documents.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('RECTIFICATION')}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
            activeTab === 'RECTIFICATION'
              ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>Rectification & Deficiency Thread</span>
        </button>
      </div>

      {/* Tab 1: Pre-Submission Readiness Check */}
      {activeTab === 'SELF_CHECK' && (
        <SelfAssessmentChecker
          initialValues={{
            locationType: currentDossier?.location_type || 'RURAL',
            landAreaAcres: 5.5,
            intake: currentDossier?.intake_proposed || 240,
            facultyTotal: 24,
            professors: 3,
            assocProfessors: 6,
            asstProfessors: 15,
            fdrLakhs: 45,
            builtUpAreaSqm: 4850,
          }}
        />
      )}

      {/* Tab 2: Document Uploader & Live Progress */}
      {activeTab === 'UPLOAD_DOCS' && (
        <div className="space-y-6">
          {activeJobId && (
            <LiveJobProgress
              jobId={activeJobId}
              onJobComplete={() => {
                refetch();
              }}
            />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <DocumentUploader
                dossierId={currentDossier?.dossier_id || 'dos-demo'}
                onUploadSuccess={() => refetch()}
                onJobStarted={(jobId) => setActiveJobId(jobId)}
              />
            </div>

            {/* Uploaded Documents List in this Dossier */}
            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Dossier Documents ({currentDossier?.documents?.length || 0})
                </h4>
                <button
                  type="button"
                  onClick={handleRunVerify}
                  disabled={verifyDossierMutation.isPending}
                  className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-semibold flex items-center gap-1 transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 ${verifyDossierMutation.isPending ? 'animate-spin' : ''}`} />
                  <span>Re-Evaluate</span>
                </button>
              </div>

              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {currentDossier?.documents && currentDossier.documents.length > 0 ? (
                  currentDossier.documents.map((doc) => (
                    <div
                      key={doc.document_id}
                      className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-bold text-white truncate max-w-[180px]">
                          {doc.title || doc.file_name}
                        </div>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 shrink-0">
                          {doc.doc_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span>{doc.page_count} Pages</span>
                        <span>•</span>
                        <span className="truncate font-mono">{doc.document_id}</span>
                      </div>
                      {doc.forensic?.is_tampered && (
                        <div className="text-[10px] text-rose-400 font-semibold flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          Tamper flags identified
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-xs text-slate-500">
                    No documents uploaded to this dossier yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Rectification Thread */}
      {activeTab === 'RECTIFICATION' && (
        <RectificationThread
          findings={currentDossier?.findings || []}
          dossierId={currentDossier?.dossier_id || 'dos-demo'}
          onRectificationSent={() => refetch()}
        />
      )}

      {/* New Dossier Registration Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel rounded-2xl p-6 max-w-lg w-full border border-slate-800 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Register New Application Dossier</h3>
              <button
                type="button"
                onClick={() => setShowNewModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDossier} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Institution Full Legal Name
                </label>
                <input
                  type="text"
                  required
                  value={newInstName}
                  onChange={(e) => setNewInstName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl glass-input text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Application Reference No.
                  </label>
                  <input
                    type="text"
                    required
                    value={newAppNo}
                    onChange={(e) => setNewAppNo(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Location Category
                  </label>
                  <select
                    value={newLocation}
                    onChange={(e) => setNewLocation(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-xs text-white"
                  >
                    <option value="RURAL">Rural</option>
                    <option value="URBAN">Urban</option>
                    <option value="MEGA_METRO">Mega Metro</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Technical Program
                  </label>
                  <select
                    value={newProgram}
                    onChange={(e) => setNewProgram(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-xs text-white"
                  >
                    <option value="ENGINEERING_AND_TECHNOLOGY">Engineering & Tech</option>
                    <option value="MANAGEMENT">Management (MBA/PGDM)</option>
                    <option value="PHARMACY">Pharmacy</option>
                    <option value="COMPUTER_APPLICATIONS">MCA / Computing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Proposed Intake
                  </label>
                  <input
                    type="number"
                    value={newIntake}
                    onChange={(e) => setNewIntake(parseInt(e.target.value) || 60)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-xs text-white"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-700 text-xs text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createDossierMutation.isPending}
                  className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition-colors"
                >
                  {createDossierMutation.isPending ? 'Registering...' : 'Create Dossier'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
