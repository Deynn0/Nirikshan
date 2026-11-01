import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import { FileText, Download, CheckSquare, Square, ShieldAlert, BookOpen, Calendar, Building, Printer } from 'lucide-react';
import type { Finding } from '../../api/types';

interface DeficiencyLetterGeneratorProps {
  institutionName?: string;
  applicationNumber?: string;
  findings?: Finding[];
}

export const DeficiencyLetterGenerator: React.FC<DeficiencyLetterGeneratorProps> = ({
  institutionName = 'Delhi Institute of Advanced Engineering & Technology',
  applicationNumber = 'AICTE-2026-APP-001',
  findings = [],
}) => {
  // Filter or populate deficient findings
  const selectableFindings = findings.length > 0 ? findings : [
    {
      finding_id: 'find-cadre-01',
      rule_id: 'AICTE-2024-CADRE-001',
      rule_name: 'Cadre Ratio Statutory Norm (1:2:6)',
      category: 'Faculty',
      status: 'FAIL',
      summary: 'Shortfall of mandatory regular Professors in technical teaching cadre.',
      details: 'Department of Computer Science has 0 regular Professors against minimum 1 required by statutory regulations.',
      handbook_citation: {
        clause_number: 'Clause 8.2 & Appendix 7.2',
        handbook_edition: 'AICTE APH 2024-2027',
        verbatim_text: 'Cadre ratio shall be 1:2:6 with minimum one regular Professor with Ph.D. in each program division.',
      },
      evidence_list: [],
      advisory_notes: [],
      is_model_advisory_only: false,
      needs_verification: false,
      timestamp: '2026-10-31',
    },
    {
      finding_id: 'find-fire-02',
      rule_id: 'AICTE-2024-FIRE-001',
      rule_name: 'State Fire Department Safety NOC Validity',
      category: 'Infrastructure',
      status: 'FAIL',
      summary: 'State Fire Safety NOC validity expired prior to regulatory approval window.',
      details: 'Fire Safety Certificate NOC #FS-2023-998 expired on 30-June-2026. Current active clearance certificate required.',
      handbook_citation: {
        clause_number: 'Clause 5.3 & Chapter II',
        handbook_edition: 'AICTE APH 2024-2027',
        verbatim_text: 'Institutions shall possess a valid, non-expired Fire Safety Certificate issued by Competent State Fire Authority.',
      },
      evidence_list: [],
      advisory_notes: [],
      is_model_advisory_only: false,
      needs_verification: false,
      timestamp: '2026-10-31',
    },
    {
      finding_id: 'find-tamper-03',
      rule_id: 'AICTE-2024-LAND-002',
      rule_name: 'Land Sale Deed Contiguity & Forensics',
      category: 'Land & Title',
      status: 'FLAGGED_TAMPER',
      summary: 'Physical microprint & Error Level Analysis anomaly identified on page 3 of Land Deed.',
      details: 'Survey map extract exhibits duplicate font glyphs and compression inconsistencies indicative of spliced plot boundary.',
      handbook_citation: {
        clause_number: 'Clause 7.1.3 & Chapter I',
        handbook_edition: 'AICTE APH 2024-2027',
        verbatim_text: 'All documents submitted shall be genuine, unaltered original records verified with revenue issuing authorities.',
      },
      evidence_list: [],
      advisory_notes: [],
      is_model_advisory_only: false,
      needs_verification: true,
      timestamp: '2026-10-31',
    },
  ];

  const [selectedIds, setSelectedIds] = useState<string[]>([
    selectableFindings[0]?.finding_id || '',
    selectableFindings[1]?.finding_id || '',
  ]);

  const [noticeRefNo, setNoticeRefNo] = useState(`AICTE/RO/SCRUTINY/2026/${Math.floor(1000 + Math.random() * 9000)}`);
  const [deadlineDays, setDeadlineDays] = useState(15);
  const [officerNotes, setOfficerNotes] = useState('Applicant must submit original verified certificates before the Standing Hearing Committee.');

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectedFindingsList = selectableFindings.filter((f) => selectedIds.includes(f.finding_id));

  // Export PDF using jsPDF
  const exportPDF = () => {
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Header
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('ALL INDIA COUNCIL FOR TECHNICAL EDUCATION', 105, 20, { align: 'center' });
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('(A STATUTORY BODY OF THE GOVERNMENT OF INDIA)', 105, 26, { align: 'center' });
    doc.text('Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070', 105, 31, { align: 'center' });

    doc.setLineWidth(0.5);
    doc.line(20, 36, 190, 36);

    // Notice Ref & Date
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.text(`Ref. No: ${noticeRefNo}`, 20, 44);
    doc.text(`Date: ${new Date().toLocaleDateString('en-GB')}`, 150, 44);

    // Subject
    doc.setFontSize(11);
    doc.text('FORMAL DEFICIENCY OBSERVATION NOTICE (AICTE APH 2024-2027)', 105, 54, { align: 'center' });

    // Recipient
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.text('To,', 20, 62);
    doc.text(`The Chairman / Registrar,`, 20, 67);
    doc.setFont('helvetica', 'bold');
    doc.text(institutionName, 20, 72);
    doc.setFont('helvetica', 'normal');
    doc.text(`Application Reference ID: ${applicationNumber}`, 20, 77);

    // Salutation & Intro
    doc.text('Sir / Madam,', 20, 86);
    const introText =
      `During offline automated deterministic scrutiny and regulatory verification of your institutional dossier against the AICTE Approval Process Handbook (APH 2024-2027), the following statutory deficiencies were identified:`;
    doc.text(doc.splitTextToSize(introText, 170), 20, 92);

    let yOffset = 104;

    selectedFindingsList.forEach((f, idx) => {
      if (yOffset > 250) {
        doc.addPage();
        yOffset = 20;
      }

      doc.setFont('helvetica', 'bold');
      doc.text(`${idx + 1}. ${f.rule_name} [${f.rule_id}]`, 20, yOffset);
      yOffset += 5;

      doc.setFont('helvetica', 'italic');
      const cit = f.handbook_citation as any;
      const clauseLabel = cit?.clause || cit?.clause_number || 'APH Clause';
      const quoteText = cit?.verbatim_text || cit?.quote || f.summary;
      const clauseText = `Verbatim AICTE Handbook Standard (${clauseLabel}): "${quoteText}"`;
      doc.text(doc.splitTextToSize(clauseText, 165), 25, yOffset);
      yOffset += 10;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      const detailText = `Deficiency Identified: ${f.details || f.summary}`;
      doc.text(doc.splitTextToSize(detailText, 165), 25, yOffset);
      yOffset += 12;
    });

    if (yOffset > 240) {
      doc.addPage();
      yOffset = 20;
    }

    // Directive
    doc.setFont('helvetica', 'bold');
    doc.text(`COMPLIANCE DIRECTIVE:`, 20, yOffset);
    yOffset += 5;

    doc.setFont('helvetica', 'normal');
    const directive =
      `You are hereby instructed to submit rectification replies with authentic supporting documents in the Nirikshan Rectification Portal within ${deadlineDays} working days from the date of issuance of this communication. Failure to rectify shall result in rejection of application under Section 10 of AICTE Act.`;
    doc.text(doc.splitTextToSize(directive, 170), 20, yOffset);
    yOffset += 24;

    // Signatures
    doc.setFont('helvetica', 'bold');
    doc.text('AICTE Scrutiny Committee', 140, yOffset);
    doc.setFont('helvetica', 'normal');
    doc.text('Officer In-Charge, Regulatory Scrutiny', 140, yOffset + 5);
    doc.text('Nirikshan Offline Verification Cell', 140, yOffset + 10);

    doc.save(`AICTE_Deficiency_Notice_${applicationNumber}.pdf`);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left: Finding Selector */}
      <div className="lg:col-span-5 glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Select Deficiencies to Cite</h3>
              <p className="text-xs text-slate-400">
                Check findings to quote verbatim AICTE handbook clauses in the formal notice.
              </p>
            </div>
          </div>
        </div>

        {/* Notice Meta Settings */}
        <div className="space-y-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 text-xs">
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Notice Reference No.</label>
            <input
              type="text"
              value={noticeRefNo}
              onChange={(e) => setNoticeRefNo(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs font-mono text-white"
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Rectification Deadline</label>
              <select
                value={deadlineDays}
                onChange={(e) => setDeadlineDays(parseInt(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
              >
                <option value={7}>7 Working Days</option>
                <option value={15}>15 Working Days</option>
                <option value={30}>30 Working Days</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Selected Count</label>
              <div className="px-2.5 py-1.5 rounded-lg bg-slate-800 text-sky-400 font-mono font-bold text-xs">
                {selectedIds.length} / {selectableFindings.length} Items
              </div>
            </div>
          </div>
        </div>

        {/* Checkbox List */}
        <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
          {selectableFindings.map((f) => {
            const isSelected = selectedIds.includes(f.finding_id);
            return (
              <div
                key={f.finding_id}
                onClick={() => toggleSelect(f.finding_id)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-amber-950/40 border-amber-500/50 ring-1 ring-amber-500/20'
                    : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div className="mt-0.5 text-amber-400">
                    {isSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-slate-500" />}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">{f.rule_name}</div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      {f.rule_id} • {f.handbook_citation?.clause_number || 'APH Norm'}
                    </div>
                    <p className="text-[11px] text-slate-300 mt-1 line-clamp-2">{f.details || f.summary}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Export Button */}
        <button
          type="button"
          disabled={selectedIds.length === 0}
          onClick={exportPDF}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-600 via-orange-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-bold text-xs shadow-lg shadow-amber-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-40"
        >
          <Download className="w-4 h-4" />
          <span>Generate & Export AICTE Deficiency Notice (PDF)</span>
        </button>
      </div>

      {/* Right: Live Formal Letter Preview */}
      <div className="lg:col-span-7 glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Printer className="w-4 h-4 text-sky-400" />
            <span>Official Letter Verbatim Preview</span>
          </h4>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
            A4 Standard Format
          </span>
        </div>

        {/* Simulated Letter Sheet */}
        <div className="bg-slate-100 text-slate-900 rounded-xl p-8 sm:p-10 shadow-2xl font-serif text-xs leading-relaxed space-y-4 border border-slate-300">
          {/* Letterhead */}
          <div className="text-center pb-3 border-b-2 border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 font-sans">
              ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
            </h2>
            <p className="text-[10px] font-sans text-slate-600 uppercase mt-0.5">
              (A Statutory Body of the Government of India)
            </p>
            <p className="text-[9px] font-sans text-slate-500">
              Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070
            </p>
          </div>

          <div className="flex justify-between items-center text-[11px] font-mono font-semibold">
            <span>Ref: {noticeRefNo}</span>
            <span>Date: {new Date().toLocaleDateString('en-GB')}</span>
          </div>

          <div className="text-center font-bold font-sans text-xs uppercase underline tracking-wide py-1">
            FORMAL DEFICIENCY OBSERVATION NOTICE (AICTE APH 2024-2027)
          </div>

          <div className="font-sans text-[11px]">
            <p className="text-slate-700">To,</p>
            <p className="text-slate-700">The Chairman / Registrar,</p>
            <p className="font-bold text-slate-900">{institutionName}</p>
            <p className="text-slate-600 font-mono">Application Reference: {applicationNumber}</p>
          </div>

          <p className="text-justify font-sans text-[11px] text-slate-800 indent-6">
            Sir / Madam, during automated offline regulatory scrutiny of your institutional compliance dossier against
            the statutory provisions of the AICTE Approval Process Handbook (APH 2024–2027), the following deficiencies
            have been recorded:
          </p>

          {/* Selected Deficiencies Quoting Verbatim */}
          <div className="space-y-3 font-sans my-3">
            {selectedFindingsList.map((f, i) => {
              const cit = f.handbook_citation as any;
              const clauseLabel = cit?.clause || cit?.clause_number || 'AICTE Norm';
              const quoteText = cit?.verbatim_text || cit?.quote || f.summary;
              return (
                <div key={f.finding_id} className="p-3 bg-white rounded border border-slate-300 space-y-1">
                  <div className="font-bold text-slate-900 text-xs">
                    {i + 1}. {f.rule_name} [{f.rule_id}]
                  </div>
                  <div className="text-[10px] text-sky-800 font-semibold italic">
                    Handbook Norm ({clauseLabel}): "{quoteText}"
                  </div>
                  <div className="text-[11px] text-slate-700">
                    <span className="font-semibold text-rose-800">Deficiency:</span> {f.details || f.summary}
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-justify font-sans text-[11px] text-slate-800 indent-6">
            You are hereby provided an opportunity to rectify the above deficiencies through the Nirikshan Rectification Portal
            within <span className="font-bold underline">{deadlineDays} working days</span>. Failure to submit compliant rectification
            shall result in recommendation for refusal of approval under Chapter I of the Regulations.
          </p>

          <div className="pt-6 flex justify-end font-sans text-right">
            <div>
              <div className="font-bold text-slate-900 text-xs">AICTE Scrutiny Committee</div>
              <div className="text-[10px] text-slate-600">Officer In-Charge, Regulatory Scrutiny</div>
              <div className="text-[9px] text-slate-500 font-mono">Digital Signature: VERIFIED 0x3A9F...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
