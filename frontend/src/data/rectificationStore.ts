export interface DeficiencyNotice {
  id: string;
  appId: string;
  institutionName: string;
  ruleClause: string;
  subject: string;
  details: string;
  deadlineDays: number;
  issuedAt: string;
  status: 'PENDING_RESPONSE' | 'SUBMITTED' | 'RESOLVED';
  institutionResponse?: string;
  uploadedDoc?: string;
  respondedAt?: string;
}

const STORAGE_KEY_DEFICIENCIES = 'nirikshan_rectification_notices';

const INITIAL_DEFICIENCIES: DeficiencyNotice[] = [
  {
    id: 'DEF-A1-001',
    appId: 'APP-2026-AICTE-4891',
    institutionName: 'Apex Institute of Technology & Management',
    ruleClause: 'Rule 2.14 / Cadre Ratio',
    subject: 'Mandatory Cadre Ratio Deficit in Computer Engineering',
    details: 'EPF-backed faculty census confirms only 1 Professor against statutory norm of 3 required for 240 intake. Submit ratified selection committee appointment orders.',
    deadlineDays: 15,
    issuedAt: '2026-03-24',
    status: 'PENDING_RESPONSE',
  },
  {
    id: 'DEF-A1-002',
    appId: 'APP-2026-AICTE-4891',
    institutionName: 'Apex Institute of Technology & Management',
    ruleClause: 'Rule 4.3 / Fire Safety NOC',
    subject: 'Municipal Fire NOC Expired on 2026-02-15',
    details: 'Fire safety certificate uploaded reflects validity expired on 15 Feb 2026. Upload current renewal endorsed by Municipal Fire Officer.',
    deadlineDays: 15,
    issuedAt: '2026-03-23',
    status: 'SUBMITTED',
    institutionResponse: 'Renewed fire safety inspection completed on 2026-03-25. Official provisional receipt and endorsed NOC attached.',
    uploadedDoc: 'MFO_Fire_NOC_Renewal_2026.pdf',
    respondedAt: '2026-03-26',
  },
  {
    id: 'DEF-A2-001',
    appId: 'APP-2026-AICTE-4892',
    institutionName: 'Trinity Polytechnic Institute',
    ruleClause: 'Rule 1.7 / Land Title Conversion',
    subject: 'Agricultural Land Non-Agriculture (NA) Conversion Incomplete',
    details: 'Survey No. 142/B revenue receipt lacks sub-divisional magistrate NA order copy. Submit certified Collector NA certificate.',
    deadlineDays: 15,
    issuedAt: '2026-03-22',
    status: 'PENDING_RESPONSE',
  },
  {
    id: 'DEF-A7-001',
    appId: 'APP-2026-AICTE-4897',
    institutionName: 'Vardhaman Institute of Technology',
    ruleClause: 'Rule 5.1 / Shared Faculty Deduplication',
    subject: 'Simultaneous Faculty Registration Detected',
    details: '3 Faculty members appear in EPF returns of both Vardhaman Institute and Apex College Solapur. Provide clarification and relieving certificates.',
    deadlineDays: 15,
    issuedAt: '2026-03-16',
    status: 'PENDING_RESPONSE',
  },
];

export function getDeficiencies(): DeficiencyNotice[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_DEFICIENCIES);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY_DEFICIENCIES, JSON.stringify(INITIAL_DEFICIENCIES));
      return INITIAL_DEFICIENCIES;
    }
    return JSON.parse(raw);
  } catch {
    return INITIAL_DEFICIENCIES;
  }
}

export function getDeficienciesForApp(appId: string): DeficiencyNotice[] {
  const all = getDeficiencies();
  const lowerApp = appId.toLowerCase();
  return all.filter(
    (d) =>
      d.appId.toLowerCase() === lowerApp ||
      (lowerApp === 'a1' && d.appId.includes('4891')) ||
      (lowerApp === 'a2' && d.appId.includes('4892')) ||
      (lowerApp === 'a3' && d.appId.includes('4893')) ||
      (lowerApp === 'a4' && d.appId.includes('4894')) ||
      (lowerApp === 'a5' && d.appId.includes('4895')) ||
      (lowerApp === 'a6' && d.appId.includes('4896')) ||
      (lowerApp === 'a7' && d.appId.includes('4897')) ||
      (lowerApp === 'a8' && d.appId.includes('4898')) ||
      (lowerApp === 'a9' && d.appId.includes('4899')) ||
      (lowerApp === 'a10' && d.appId.includes('4900')) ||
      (lowerApp === 'a11' && d.appId.includes('4901'))
  );
}

export function issueDeficiencyNotice(notice: Omit<DeficiencyNotice, 'id' | 'issuedAt' | 'status'>): DeficiencyNotice {
  const all = getDeficiencies();
  const newNotice: DeficiencyNotice = {
    ...notice,
    id: `DEF-REG-${Date.now().toString(36).toUpperCase()}`,
    issuedAt: new Date().toISOString().split('T')[0],
    status: 'PENDING_RESPONSE',
  };
  const updated = [newNotice, ...all];
  try {
    localStorage.setItem(STORAGE_KEY_DEFICIENCIES, JSON.stringify(updated));
    window.dispatchEvent(new Event('nirikshan-deficiencies-changed'));
  } catch (e) {
    console.error('Failed to save deficiency notice', e);
  }
  return newNotice;
}

export function respondToDeficiency(
  deficiencyId: string,
  institutionResponse: string,
  uploadedDoc?: string
): boolean {
  const all = getDeficiencies();
  const index = all.findIndex((d) => d.id === deficiencyId);
  if (index === -1) return false;
  all[index] = {
    ...all[index],
    institutionResponse,
    uploadedDoc: uploadedDoc || 'Rectified_Statutory_Evidence.pdf',
    respondedAt: new Date().toISOString().split('T')[0],
    status: 'SUBMITTED',
  };
  try {
    localStorage.setItem(STORAGE_KEY_DEFICIENCIES, JSON.stringify(all));
    window.dispatchEvent(new Event('nirikshan-deficiencies-changed'));
  } catch (e) {
    console.error('Failed to update deficiency response', e);
  }
  return true;
}
