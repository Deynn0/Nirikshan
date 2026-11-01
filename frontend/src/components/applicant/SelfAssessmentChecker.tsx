import React, { useState, useMemo } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, BookOpen, Calculator, Sparkles, HelpCircle } from 'lucide-react';

interface ReadinessRule {
  id: string;
  name: string;
  category: string;
  handbookClause: string;
  verbatimNorm: string;
  status: 'PASS' | 'WARNING' | 'FAIL';
  currentValue: string;
  requiredValue: string;
  details: string;
}

interface SelfAssessmentCheckerProps {
  initialValues?: {
    locationType?: string;
    landAreaAcres?: number;
    intake?: number;
    facultyTotal?: number;
    professors?: number;
    assocProfessors?: number;
    asstProfessors?: number;
    fdrLakhs?: number;
    builtUpAreaSqm?: number;
  };
  onApplyParameters?: (params: any) => void;
}

export const SelfAssessmentChecker: React.FC<SelfAssessmentCheckerProps> = ({
  initialValues,
  onApplyParameters,
}) => {
  const [locationType, setLocationType] = useState<string>(initialValues?.locationType || 'RURAL');
  const [landArea, setLandArea] = useState<number>(initialValues?.landAreaAcres ?? 5.2);
  const [intake, setIntake] = useState<number>(initialValues?.intake ?? 240);
  const [facultyCount, setFacultyCount] = useState<number>(initialValues?.facultyTotal ?? 16);
  const [professors, setProfessors] = useState<number>(initialValues?.professors ?? 2);
  const [assocProfessors, setAssocProfessors] = useState<number>(initialValues?.assocProfessors ?? 4);
  const [asstProfessors, setAsstProfessors] = useState<number>(initialValues?.asstProfessors ?? 10);
  const [fdrAmount, setFdrAmount] = useState<number>(initialValues?.fdrLakhs ?? 40);
  const [builtUpArea, setBuiltUpArea] = useState<number>(initialValues?.builtUpAreaSqm ?? 4200);

  // Keep facultyCount in sync with sum of cadres if edited
  const sumCadre = professors + assocProfessors + asstProfessors;

  // Real-time evaluation against AICTE APH 2024-2027 statutory rules
  const evaluatedRules: ReadinessRule[] = useMemo(() => {
    const rules: ReadinessRule[] = [];

    // 1. Land Area Norm
    const minLandRequired = locationType === 'RURAL' ? 5.0 : locationType === 'URBAN' ? 2.5 : 1.5;
    const landStatus: 'PASS' | 'WARNING' | 'FAIL' =
      landArea >= minLandRequired
        ? 'PASS'
        : landArea >= minLandRequired * 0.9
        ? 'WARNING'
        : 'FAIL';

    rules.push({
      id: 'AICTE-2024-LAND-001',
      name: 'Minimum Campus Land Area',
      category: 'Infrastructure',
      handbookClause: 'APH 2024-27 Clause 7.1 & Appendix 4.1',
      verbatimNorm: `Technical Engineering institutes must possess minimum ${minLandRequired} acres in a single contiguous parcel in ${locationType} category.`,
      status: landStatus,
      currentValue: `${landArea} Acres (${locationType})`,
      requiredValue: `>= ${minLandRequired} Acres`,
      details:
        landStatus === 'PASS'
          ? `Compliant. Your land parcel exceeds the minimum requirement by ${(landArea - minLandRequired).toFixed(2)} acres.`
          : `Deficiency: Deficit of ${(minLandRequired - landArea).toFixed(2)} acres. Formal submission will be rejected by AICTE Scrutiny Committee.`,
    });

    // 2. Student : Faculty Ratio (SFR)
    // AICTE norm for UG Engineering: 1:20 SFR. Total students approx intake * 4 years = 240 * 4 = 960 (for 4 years) or first year intake / 20 = 12 faculty for year 1
    const requiredFacultyForIntake = Math.ceil(intake / 15); // for active year cohorts
    const currentSFR = facultyCount > 0 ? (intake / facultyCount).toFixed(1) : '0';
    const sfrStatus: 'PASS' | 'WARNING' | 'FAIL' =
      facultyCount >= requiredFacultyForIntake
        ? 'PASS'
        : facultyCount >= requiredFacultyForIntake - 2
        ? 'WARNING'
        : 'FAIL';

    rules.push({
      id: 'AICTE-2024-FACULTY-001',
      name: 'Student-to-Faculty Ratio (SFR)',
      category: 'Academic Faculty',
      handbookClause: 'APH 2024-27 Clause 8.2 & Appendix 7.1',
      verbatimNorm: 'UG Technical Engineering programs must maintain a minimum Student : Faculty ratio not exceeding 20:1 across departments.',
      status: sfrStatus,
      currentValue: `${facultyCount} Faculty (SFR approx 1:${currentSFR})`,
      requiredValue: `>= ${requiredFacultyForIntake} Faculty`,
      details:
        sfrStatus === 'PASS'
          ? `Compliant. Faculty roster meets AICTE staffing thresholds for intake of ${intake}.`
          : `Deficiency: You require at least ${requiredFacultyForIntake - facultyCount} additional faculty members to avoid scrutiny deficiency notice.`,
    });

    // 3. Cadre Ratio 1 : 2 : 6
    // For every 1 Professor, there should be 2 Associate Professors and 6 Assistant Professors
    // Minimum 1 Professor is mandatory per department
    const cadreStatus: 'PASS' | 'WARNING' | 'FAIL' =
      professors >= 1 && assocProfessors >= 2 && asstProfessors >= 6
        ? 'PASS'
        : professors >= 1
        ? 'WARNING'
        : 'FAIL';

    rules.push({
      id: 'AICTE-2024-CADRE-001',
      name: 'Cadre Distribution Ratio (1:2:6)',
      category: 'Academic Faculty',
      handbookClause: 'APH 2024-27 Appendix 7.2',
      verbatimNorm: 'Academic staff cadre ratio shall be 1 Professor : 2 Associate Professors : 6 Assistant Professors with at least 1 Professor per department.',
      status: cadreStatus,
      currentValue: `${professors} Prof : ${assocProfessors} Assoc Prof : ${asstProfessors} Asst Prof`,
      requiredValue: '1 : 2 : 6 Cadre Ratio',
      details:
        cadreStatus === 'PASS'
          ? 'Compliant. Cadre distribution fulfills statutory ratio requirements.'
          : professors < 1
          ? 'Critical Violation: At least 1 full-time regular Professor with Ph.D. is mandatory.'
          : 'Warning: Ratio of Associate Professors to Assistant Professors is skewed. AICTE may issue advisory.',
    });

    // 4. Joint Fixed Deposit Receipt (FDR)
    const minFdrLakhs = 35.0;
    const fdrStatus: 'PASS' | 'WARNING' | 'FAIL' =
      fdrAmount >= minFdrLakhs
        ? 'PASS'
        : fdrAmount >= minFdrLakhs * 0.8
        ? 'WARNING'
        : 'FAIL';

    rules.push({
      id: 'AICTE-2024-FDR-001',
      name: 'Joint Security Deposit FDR',
      category: 'Financial Viability',
      handbookClause: 'APH 2024-27 Clause 6.4',
      verbatimNorm: 'Technical institute applicants must maintain a Joint FDR of at least ₹35.00 Lakhs in nationalized bank jointly with AICTE Chairman/RO.',
      status: fdrStatus,
      currentValue: `₹${fdrAmount.toFixed(2)} Lakhs`,
      requiredValue: `>= ₹${minFdrLakhs.toFixed(2)} Lakhs`,
      details:
        fdrStatus === 'PASS'
          ? `Compliant. Deposit exceeds statutory minimum by ₹${(fdrAmount - minFdrLakhs).toFixed(2)} Lakhs.`
          : `Deficiency: Joint FDR is short by ₹${(minFdrLakhs - fdrAmount).toFixed(2)} Lakhs.`,
    });

    // 5. Total Instructional Built-up Area
    const minAreaSqm = 4000.0;
    const areaStatus: 'PASS' | 'WARNING' | 'FAIL' =
      builtUpArea >= minAreaSqm
        ? 'PASS'
        : builtUpArea >= minAreaSqm * 0.9
        ? 'WARNING'
        : 'FAIL';

    rules.push({
      id: 'AICTE-2024-AREA-001',
      name: 'Total Built-up Instructional Area',
      category: 'Infrastructure',
      handbookClause: 'APH 2024-27 Appendix 4.2',
      verbatimNorm: 'Approved building plans must guarantee at least 4,000 sqm of carpet area for instructional and administrative requirements.',
      status: areaStatus,
      currentValue: `${builtUpArea.toLocaleString()} sqm`,
      requiredValue: `>= ${minAreaSqm.toLocaleString()} sqm`,
      details:
        areaStatus === 'PASS'
          ? 'Compliant. Built-up area exceeds approved master plan norm.'
          : `Deficiency: Shortfall of ${(minAreaSqm - builtUpArea).toFixed(0)} sqm in instructional space.`,
    });

    return rules;
  }, [locationType, landArea, intake, facultyCount, professors, assocProfessors, asstProfessors, fdrAmount, builtUpArea]);

  // Overall readiness score
  const passCount = evaluatedRules.filter((r) => r.status === 'PASS').length;
  const warningCount = evaluatedRules.filter((r) => r.status === 'WARNING').length;
  const failCount = evaluatedRules.filter((r) => r.status === 'FAIL').length;
  const readinessPercent = Math.round((passCount / evaluatedRules.length) * 100);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Self-Assessment Readiness Check
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-500/30 font-normal">
                  Pre-Submission Audit
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Simulate deterministic scrutiny against AICTE Approval Process Handbook (APH 2024–2027) norms before filing.
              </p>
            </div>
          </div>
        </div>

        {/* Readiness Meter */}
        <div className="flex items-center gap-4 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
          <div className="text-right">
            <div className="text-xs text-slate-400 font-medium">Readiness Index</div>
            <div
              className={`text-xl font-black font-mono ${
                failCount === 0 ? 'text-emerald-400' : failCount === 1 ? 'text-amber-400' : 'text-rose-400'
              }`}
            >
              {readinessPercent}%
            </div>
          </div>
          <div className="flex gap-1.5 text-xs font-semibold">
            <span className="px-2 py-1 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
              {passCount} Pass
            </span>
            {warningCount > 0 && (
              <span className="px-2 py-1 rounded bg-amber-950/60 text-amber-300 border border-amber-500/30">
                {warningCount} Warn
              </span>
            )}
            {failCount > 0 && (
              <span className="px-2 py-1 rounded bg-rose-950/60 text-rose-300 border border-rose-500/30">
                {failCount} Fail
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Input Parameters Form */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-800/80">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Campus Location Category
          </label>
          <select
            value={locationType}
            onChange={(e) => setLocationType(e.target.value)}
            className="w-full px-3 py-2 rounded-lg glass-input text-xs text-white"
          >
            <option value="RURAL">Rural (Norm: 5.0 Acres)</option>
            <option value="URBAN">Urban / Municipal (Norm: 2.5 Acres)</option>
            <option value="MEGA_METRO">Mega Metro City (Norm: 1.5 Acres)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Land Area (Acres)
          </label>
          <input
            type="number"
            step="0.05"
            min="0"
            value={landArea}
            onChange={(e) => setLandArea(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 rounded-lg glass-input text-xs text-white"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Proposed Total Intake (Students)
          </label>
          <input
            type="number"
            step="30"
            min="30"
            value={intake}
            onChange={(e) => setIntake(parseInt(e.target.value) || 30)}
            className="w-full px-3 py-2 rounded-lg glass-input text-xs text-white"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Professors (Full Time)
          </label>
          <input
            type="number"
            min="0"
            value={professors}
            onChange={(e) => {
              const val = parseInt(e.target.value) || 0;
              setProfessors(val);
              setFacultyCount(val + assocProfessors + asstProfessors);
            }}
            className="w-full px-3 py-2 rounded-lg glass-input text-xs text-white"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Associate & Asst. Professors
          </label>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              placeholder="Assoc"
              min="0"
              value={assocProfessors}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 0;
                setAssocProfessors(val);
                setFacultyCount(professors + val + asstProfessors);
              }}
              className="w-full px-2.5 py-2 rounded-lg glass-input text-xs text-white"
            />
            <input
              type="number"
              placeholder="Asst"
              min="0"
              value={asstProfessors}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 0;
                setAsstProfessors(val);
                setFacultyCount(professors + assocProfessors + val);
              }}
              className="w-full px-2.5 py-2 rounded-lg glass-input text-xs text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Joint FDR Amount (₹ Lakhs)
          </label>
          <input
            type="number"
            step="1"
            min="0"
            value={fdrAmount}
            onChange={(e) => setFdrAmount(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 rounded-lg glass-input text-xs text-white"
          />
        </div>
      </div>

      {/* Evaluated Rule Cards */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Statutory Verification Matrix ({evaluatedRules.length} Rules Evaluated)
        </h4>

        <div className="grid grid-cols-1 gap-3">
          {evaluatedRules.map((rule) => {
            const isPass = rule.status === 'PASS';
            const isWarn = rule.status === 'WARNING';
            const isFail = rule.status === 'FAIL';

            return (
              <div
                key={rule.id}
                className={`p-4 rounded-xl border transition-all ${
                  isPass
                    ? 'bg-slate-900/60 border-emerald-500/30'
                    : isWarn
                    ? 'bg-amber-950/20 border-amber-500/40'
                    : 'bg-rose-950/30 border-rose-500/40 ring-1 ring-rose-500/20'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 shrink-0">
                      {isPass && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                      {isWarn && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                      {isFail && <XCircle className="w-5 h-5 text-rose-400" />}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-sm text-white">{rule.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {rule.id}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-500/30">
                          {rule.category}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{rule.details}</p>
                      
                      {/* Handbook Clause Citation */}
                      <div className="mt-2 flex items-center gap-1.5 text-[11px] text-sky-400 font-mono">
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Citation: {rule.handbookClause}</span>
                      </div>
                    </div>
                  </div>

                  {/* Status Badge & Values */}
                  <div className="text-right shrink-0">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-md text-xs font-bold tracking-wide ${
                        isPass
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : isWarn
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      }`}
                    >
                      {rule.status}
                    </span>
                    <div className="mt-1.5 text-[11px] text-slate-300 font-mono">
                      Current: <span className="font-semibold text-white">{rule.currentValue}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Norm: {rule.requiredValue}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
