import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, MessageSquare, Send, Paperclip, Clock, ShieldAlert, FileText, ArrowUpRight } from 'lucide-react';
import type { Finding } from '../../api/types';

interface RectificationItem {
  id: string;
  findingId: string;
  ruleId: string;
  deficiencyTitle: string;
  clauseCitation: string;
  officerComment: string;
  applicantReply?: string;
  attachedFile?: string;
  status: 'OPEN_DEFICIENCY' | 'RECTIFICATION_SUBMITTED' | 'RESOLVED_BY_COMMITTEE';
  updatedAt: string;
}

interface RectificationThreadProps {
  findings?: Finding[];
  dossierId: string;
  onRectificationSent?: () => void;
}

export const RectificationThread: React.FC<RectificationThreadProps> = ({
  findings = [],
  dossierId,
  onRectificationSent,
}) => {
  // Extract deficient or manual review findings
  const deficientFindings = findings.filter(
    (f) => f.status === 'FAIL' || f.status === 'MANUAL_REVIEW_REQUIRED' || f.status === 'FLAGGED_TAMPER'
  );

  // Initial rectification items state
  const [threads, setThreads] = useState<RectificationItem[]>(() => {
    if (deficientFindings.length > 0) {
      return deficientFindings.map((f, i) => ({
        id: `rec-${i + 1}`,
        findingId: f.finding_id,
        ruleId: f.rule_id,
        deficiencyTitle: f.rule_name || f.summary,
        clauseCitation: (f.handbook_citation as any)?.clause
          ? `${(f.handbook_citation as any).clause} (${(f.handbook_citation as any).edition || 'APH 2024-2027'})`
          : 'AICTE APH 2024-2027 Chapter VII',
        officerComment: f.details || f.summary,
        status: 'OPEN_DEFICIENCY',
        updatedAt: '2026-10-31 16:30',
      }));
    }
    // Fallback sample deficiency items for interactive demonstration
    return [
      {
        id: 'rec-1',
        findingId: 'find-cadre-01',
        ruleId: 'AICTE-2024-CADRE-001',
        deficiencyTitle: 'Shortfall in Mandatory Professor Cadre Ratio (1:2:6)',
        clauseCitation: 'APH 2024-27 Appendix 7.2',
        officerComment: 'Department of Computer Science currently records 0 regular professors against minimum 1 required by statutory regulations.',
        applicantReply: 'We have appointed Dr. S. Ramanujan (Ph.D. IIT Delhi) as full-time Professor vide appointment order IITD-CS-2026/04 dated 15-Oct-2026.',
        attachedFile: 'Appointment_Order_Ramanujan.pdf',
        status: 'RECTIFICATION_SUBMITTED',
        updatedAt: '2026-10-31 17:15',
      },
      {
        id: 'rec-2',
        findingId: 'find-fire-02',
        ruleId: 'AICTE-2024-FIRE-001',
        deficiencyTitle: 'State Fire Department Safety NOC Validity Expired',
        clauseCitation: 'APH 2024-27 Clause 5.3',
        officerComment: 'Submitted Fire NOC expired on 30-June-2026. Current active certificate required prior to final committee clearance.',
        status: 'OPEN_DEFICIENCY',
        updatedAt: '2026-10-31 15:40',
      },
    ];
  });

  const [activeReplyId, setActiveReplyId] = useState<string | null>(threads[1]?.id || threads[0]?.id || null);
  const [replyText, setReplyText] = useState('');
  const [attachedFileName, setAttachedFileName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successToast, setSuccessToast] = useState(false);

  const handleSendReply = (threadId: string) => {
    if (!replyText.trim()) return;
    setIsSubmitting(true);

    setTimeout(() => {
      setThreads((prev) =>
        prev.map((t) =>
          t.id === threadId
            ? {
                ...t,
                applicantReply: replyText,
                attachedFile: attachedFileName || 'Affidavit_Clarification.pdf',
                status: 'RECTIFICATION_SUBMITTED',
                updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              }
            : t
        )
      );
      setReplyText('');
      setAttachedFileName('');
      setIsSubmitting(false);
      setSuccessToast(true);
      setTimeout(() => setSuccessToast(false), 4000);
      if (onRectificationSent) onRectificationSent();
    }, 600);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Rectification & Deficiency Resolution Thread
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-amber-300 font-mono">
                  {threads.filter((t) => t.status === 'OPEN_DEFICIENCY').length} Pending Deficiencies
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Submit point-by-point compliance clarifications and supplemental evidence in response to scrutiny observations.
              </p>
            </div>
          </div>
        </div>

        {successToast && (
          <div className="px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-200 text-xs font-medium flex items-center gap-1.5 animate-bounce">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Rectification recorded for scrutiny review</span>
          </div>
        )}
      </div>

      {/* Deficiency Threads List */}
      <div className="space-y-4">
        {threads.map((item) => {
          const isOpen = item.status === 'OPEN_DEFICIENCY';
          const isSubmitted = item.status === 'RECTIFICATION_SUBMITTED';

          return (
            <div
              key={item.id}
              className={`rounded-xl border transition-all ${
                isOpen
                  ? 'bg-slate-900/60 border-amber-500/40'
                  : 'bg-slate-900/40 border-slate-800'
              }`}
            >
              {/* Item Header */}
              <div className="p-4 border-b border-slate-800/80 flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isOpen ? (
                      <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      {item.deficiencyTitle}
                    </h4>
                    <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] font-mono">
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {item.ruleId}
                      </span>
                      <span className="text-sky-400">
                        Clause: {item.clauseCitation}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span
                    className={`inline-block px-2.5 py-1 rounded text-[11px] font-bold ${
                      isOpen
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}
                  >
                    {isOpen ? 'ACTION REQUIRED' : 'RECTIFICATION SUBMITTED'}
                  </span>
                  <div className="text-[10px] text-slate-500 mt-1 font-mono">{item.updatedAt}</div>
                </div>
              </div>

              {/* Thread Content */}
              <div className="p-4 space-y-3">
                {/* Officer Observation */}
                <div className="bg-slate-950/70 rounded-xl p-3 border border-slate-800 text-xs">
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-1 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                    AICTE Scrutiny Officer Observation
                  </div>
                  <p className="text-slate-300 leading-relaxed">{item.officerComment}</p>
                </div>

                {/* Applicant Existing Reply if submitted */}
                {item.applicantReply && (
                  <div className="bg-sky-950/30 rounded-xl p-3 border border-sky-500/30 text-xs">
                    <div className="text-[10px] uppercase font-bold text-sky-300 mb-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                      Institution Rectification Reply
                    </div>
                    <p className="text-slate-200 leading-relaxed">{item.applicantReply}</p>
                    {item.attachedFile && (
                      <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-700 text-[11px] text-sky-300 font-mono">
                        <FileText className="w-3.5 h-3.5" />
                        <span>{item.attachedFile}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Reply Form for Open Deficiency */}
                {isOpen && (
                  <div className="pt-2 space-y-2">
                    <label className="block text-xs font-semibold text-slate-300">
                      Write Institutional Rectification & Justification:
                    </label>
                    <textarea
                      rows={3}
                      value={activeReplyId === item.id ? replyText : ''}
                      onChange={(e) => {
                        setActiveReplyId(item.id);
                        setReplyText(e.target.value);
                      }}
                      placeholder="Specify corrective action taken, resolution order number, or upload evidence..."
                      className="w-full p-3 rounded-xl glass-input text-xs text-white placeholder-slate-500 resize-none"
                    />

                    <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-1">
                      <div className="flex items-center gap-2 w-full sm:w-auto">
                        <label
                          htmlFor={`file-attach-${item.id}`}
                          className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-300 cursor-pointer flex items-center gap-1.5 transition-colors"
                        >
                          <Paperclip className="w-3.5 h-3.5 text-sky-400" />
                          <span>{attachedFileName || 'Attach Proof PDF'}</span>
                        </label>
                        <input
                          id={`file-attach-${item.id}`}
                          type="file"
                          className="hidden"
                          onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                              setAttachedFileName(e.target.files[0].name);
                            }
                          }}
                        />
                      </div>

                      <button
                        type="button"
                        disabled={isSubmitting || !replyText.trim() || activeReplyId !== item.id}
                        onClick={() => handleSendReply(item.id)}
                        className="w-full sm:w-auto px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 disabled:opacity-40"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Submit Rectification Reply</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
