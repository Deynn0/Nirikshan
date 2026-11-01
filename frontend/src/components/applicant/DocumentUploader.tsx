import React, { useState } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, Plus, Sparkles, Shield, ArrowRight } from 'lucide-react';
import { useUploadDocument, useSubmitJob } from '../../api/hooks';

const DOCUMENT_TYPES = [
  { value: 'LAND_SALE_DEED', label: 'Land Registered Sale Deed', category: 'Land & Title' },
  { value: 'LAND_LEASE_DEED', label: 'Land 30-Year Registered Lease Deed', category: 'Land & Title' },
  { value: 'LAND_USE_CONVERSION_CERT', label: 'Land Use Conversion Certificate (NA/CLU)', category: 'Land & Title' },
  { value: 'BUILDING_PLAN_APPROVED', label: 'Competent Authority Approved Building Plan', category: 'Infrastructure' },
  { value: 'OCCUPANCY_CERTIFICATE', label: 'Building Completion & Occupancy Certificate', category: 'Infrastructure' },
  { value: 'FIRE_SAFETY_NOC', label: 'State Fire Department Safety NOC', category: 'Safety' },
  { value: 'FACULTY_LIST_ROSTER', label: 'Faculty Roster with Cadre & Qualifications', category: 'Academic' },
  { value: 'FDR_CERTIFICATE', label: 'Joint Fixed Deposit Receipt (FDR ₹35L+)', category: 'Finance' },
  { value: 'TRUST_REGISTRATION_CERT', label: 'Society / Trust Registration Certificate', category: 'Legal Entity' },
  { value: 'AICTE_APPROVAL_LETTER', label: 'Previous AICTE Extension of Approval (EOA)', category: 'Prior Approvals' },
  { value: 'AFFIDAVIT_SELF_DECLARATION', label: 'Standard AICTE Affidavit (Self-declaration)', category: 'Affidavit' },
];

interface DocumentUploaderProps {
  dossierId: string;
  onUploadSuccess?: () => void;
  onJobStarted?: (jobId: string) => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  dossierId,
  onUploadSuccess,
  onJobStarted,
}) => {
  const [docType, setDocType] = useState('LAND_SALE_DEED');
  const [title, setTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSelfAttested, setIsSelfAttested] = useState(true);

  // Parameter fields
  const [landArea, setLandArea] = useState<string>('5.5');
  const [surveyNo, setSurveyNo] = useState<string>('Plot-44/A, Sector-9');
  const [facultyCount, setFacultyCount] = useState<string>('24');
  const [professors, setProfessors] = useState<string>('3');
  const [assocProfessors, setAssocProfessors] = useState<string>('6');
  const [asstProfessors, setAsstProfessors] = useState<string>('15');
  const [fdrAmount, setFdrAmount] = useState<string>('45.0');
  const [builtUpArea, setBuiltUpArea] = useState<string>('4850');

  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadMutation = useUploadDocument();
  const submitJobMutation = useSubmitJob();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      if (!title) {
        setTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      if (!title) {
        setTitle(e.dataTransfer.files[0].name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file to upload');
      return;
    }
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('doc_type', docType);
    formData.append('title', title || selectedFile.name);
    formData.append('is_self_attested', String(isSelfAttested));

    if (landArea) formData.append('land_area_acres', landArea);
    if (surveyNo) formData.append('survey_no', surveyNo);
    if (facultyCount) formData.append('faculty_count', facultyCount);
    if (professors) formData.append('cadre_professors', professors);
    if (assocProfessors) formData.append('cadre_assoc_professors', assocProfessors);
    if (asstProfessors) formData.append('cadre_asst_professors', asstProfessors);
    if (fdrAmount) formData.append('fdr_amount_lakhs', fdrAmount);
    if (builtUpArea) formData.append('built_up_area_sqm', builtUpArea);

    try {
      await uploadMutation.mutateAsync({ dossierId, formData });
      setSelectedFile(null);
      setTitle('');
      if (onUploadSuccess) onUploadSuccess();

      // Automatically trigger scrutiny evaluation job via SSE
      const job = await submitJobMutation.mutateAsync(dossierId);
      if (onJobStarted && job?.job_id) {
        onJobStarted(job.job_id);
      }
    } catch (err: any) {
      setUploadError(err?.message || 'Failed to upload document');
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Upload Regulatory Document
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-500/30">
              Quarantine Enclave
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Files are quarantined with AES-256 envelope encryption and inspected by sandboxed isolated workers.
          </p>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      <form onSubmit={handleUpload} className="space-y-4">
        {/* Document Category Dropdown */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Regulatory Document Type <span className="text-rose-400">*</span>
          </label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl glass-input text-xs text-white"
          >
            {DOCUMENT_TYPES.map((dt) => (
              <option key={dt.value} value={dt.value} className="bg-slate-900 text-white">
                [{dt.category}] {dt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-sky-400 bg-sky-950/20'
              : selectedFile
              ? 'border-emerald-500/50 bg-emerald-950/10'
              : 'border-slate-700 hover:border-slate-500 bg-slate-900/30'
          }`}
          onClick={() => document.getElementById('doc-file-input')?.click()}
        >
          <input
            id="doc-file-input"
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            onChange={handleFileChange}
          />
          <div className="flex flex-col items-center justify-center gap-2">
            <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-300">
              {selectedFile ? (
                <File className="w-6 h-6 text-emerald-400" />
              ) : (
                <UploadCloud className="w-6 h-6 text-sky-400" />
              )}
            </div>
            {selectedFile ? (
              <div>
                <p className="text-xs font-bold text-white">{selectedFile.name}</p>
                <p className="text-[11px] text-slate-400 font-mono">
                  {(selectedFile.size / 1024).toFixed(1)} KB — Ready to upload
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-medium text-slate-200">
                  Drag and drop regulatory PDF or image here, or browse
                </p>
                <p className="text-[10px] text-slate-500 mt-1">
                  Supported: PDF (single & multi-page), TIFF, JPG, PNG (Max 50MB)
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Extracted / Input Metadata Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 bg-slate-900/40 p-3.5 rounded-xl border border-slate-800">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              Document Display Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Registered Sale Deed Vol-3"
              className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
            />
          </div>

          {(docType.includes('LAND') || docType === 'BUILDING_PLAN_APPROVED') && (
            <>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Land Area in Acres
                </label>
                <input
                  type="text"
                  value={landArea}
                  onChange={(e) => setLandArea(e.target.value)}
                  placeholder="5.5"
                  className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Survey / Khasra No.
                </label>
                <input
                  type="text"
                  value={surveyNo}
                  onChange={(e) => setSurveyNo(e.target.value)}
                  placeholder="e.g. 44/A, Plot 9"
                  className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
                />
              </div>
            </>
          )}

          {docType === 'FACULTY_LIST_ROSTER' && (
            <>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Total Faculty Count
                </label>
                <input
                  type="number"
                  value={facultyCount}
                  onChange={(e) => setFacultyCount(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                  Professors / Assoc / Asst
                </label>
                <div className="grid grid-cols-3 gap-1">
                  <input
                    type="number"
                    placeholder="Prof"
                    value={professors}
                    onChange={(e) => setProfessors(e.target.value)}
                    className="w-full px-1.5 py-1.5 rounded-lg glass-input text-xs text-white"
                  />
                  <input
                    type="number"
                    placeholder="Assoc"
                    value={assocProfessors}
                    onChange={(e) => setAssocProfessors(e.target.value)}
                    className="w-full px-1.5 py-1.5 rounded-lg glass-input text-xs text-white"
                  />
                  <input
                    type="number"
                    placeholder="Asst"
                    value={asstProfessors}
                    onChange={(e) => setAsstProfessors(e.target.value)}
                    className="w-full px-1.5 py-1.5 rounded-lg glass-input text-xs text-white"
                  />
                </div>
              </div>
            </>
          )}

          {docType === 'FDR_CERTIFICATE' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                FDR Principal Amount (₹ Lakhs)
              </label>
              <input
                type="number"
                value={fdrAmount}
                onChange={(e) => setFdrAmount(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
              />
            </div>
          )}

          {docType === 'BUILDING_PLAN_APPROVED' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                Approved Built-Up Area (sqm)
              </label>
              <input
                type="number"
                value={builtUpArea}
                onChange={(e) => setBuiltUpArea(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
              />
            </div>
          )}
        </div>

        {/* Self Attested Checkbox */}
        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="self-attested-chk"
            checked={isSelfAttested}
            onChange={(e) => setIsSelfAttested(e.target.checked)}
            className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-sky-600 focus:ring-0"
          />
          <label htmlFor="self-attested-chk" className="text-xs text-slate-300 cursor-pointer">
            Document is authenticated with institutional stamp and digital/wet signature
          </label>
        </div>

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={uploadMutation.isPending || submitJobMutation.isPending || !selectedFile}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white font-semibold text-xs shadow-lg shadow-sky-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {uploadMutation.isPending || submitJobMutation.isPending ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Encrypting & Enclave Ingestion...</span>
              </div>
            ) : (
              <>
                <span>Upload & Initiate AICTE Scrutiny Pipeline</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
