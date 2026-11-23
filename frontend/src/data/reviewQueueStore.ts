import { ApplicationItem, FindingDetail } from './mockScrutinyData';

const STORAGE_KEY_APPS = 'nirikshan_analysed_applications';
const STORAGE_KEY_FINDINGS = 'nirikshan_analysed_findings';

export interface AnalysedDocPayload {
  filename: string;
  filesize?: number;
  isTampered?: boolean;
  sha256?: string;
  institutionName?: string;
  category?: 'Engineering' | 'Management' | 'Pharmacy' | 'Polytechnic';
  location?: string;
  tamperDetail?: string;
  signatureDetail?: string;
  trustLadder?: string;
}

export function getAnalysedApplications(): ApplicationItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_APPS);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to read analysed applications from storage', e);
    return [];
  }
}

export function getAnalysedFindingsForApp(appId: string): FindingDetail[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_FINDINGS);
    if (!raw) return [];
    const allFindings: Record<string, FindingDetail[]> = JSON.parse(raw);
    return allFindings[appId] || [];
  } catch (e) {
    console.error('Failed to read findings from storage', e);
    return [];
  }
}

export function addAnalysedDocumentToReviewQueue(payload: AnalysedDocPayload): {
  app: ApplicationItem;
  finding: FindingDetail;
} {
  const isTampered = payload.isTampered ?? true;
  const shortHash = (payload.sha256 || '4d83e2f1839a').slice(0, 8);
  const appId = `APP-2026-REV-${shortHash.toUpperCase()}`;

  // Derive institution name from filename if not supplied
  let derivedName = payload.institutionName;
  if (!derivedName) {
    if (payload.filename.toLowerCase().includes('builtup')) {
      derivedName = 'Apex Built-up Verification · ' + payload.filename;
    } else if (payload.filename.toLowerCase().includes('lease')) {
      derivedName = 'Pune Sub-Registrar Lease Verification · ' + payload.filename;
    } else {
      derivedName = `Dossier: ${payload.filename.replace(/\.[^/.]+$/, '')}`;
    }
  }

  const appItem: ApplicationItem = {
    id: appId,
    name: derivedName,
    category: payload.category || 'Engineering',
    status: isTampered ? 'Needs attention' : 'Under review',
    statusType: isTampered ? 'critical' : 'neutral',
    openFindings: isTampered ? 1 : 0,
    riskScore: isTampered ? 88 : 24,
    location: payload.location || 'Pune, Maharashtra (WRO Directorate)',
    submittedAt: new Date().toISOString().split('T')[0],
    strongestProof: payload.trustLadder || (isTampered ? 'E1 (Downgraded from E4)' : 'E4 Digilocker Validated'),
  };

  const findingItem: FindingDetail = {
    id: `FND-${shortHash.toUpperCase()}-01`,
    group: 'Document forensics',
    title: isTampered
      ? `PDF Stream Tampering / Incremental Append (${payload.filename})`
      : `Document Authenticity Verification (${payload.filename})`,
    severity: isTampered ? 'critical' : 'verified',
    severityLabel: isTampered ? 'High Risk Tamper' : 'Authentic Stream',
    ruleId: 'RULE-SEC-04',
    description:
      payload.tamperDetail ||
      (isTampered
        ? `Incremental append detected in ${payload.filename} post-digital signature at byte 0x004F8A20. Visual carpet area altered after digital signing.`
        : `All cryptographic checks passed for ${payload.filename}. No post-signing modifications detected.`),
    recommendation: isTampered
      ? 'Forward to AICTE Regional Standing Hearing Committee. Require original physical deed verification.'
      : 'Document accepted into standard verification stream.',
    documentRef: payload.filename,
    pageNumber: 1,
    evidenceSnippet: isTampered
      ? 'xref table offset modified; trailer /Prev pointer points to secondary xref block.'
      : 'Single continuous xref table; valid cryptographic hash.',
    evidenceHash: payload.sha256 || '4d83e2f1839a829104ebc7612c77d9401bf5199859f14ba6',
    statutoryReference: 'AICTE Approval Process Handbook (APH 2026-27) Appendix 4 & IT Act 2000 Section 65B',
  };

  try {
    const existingApps = getAnalysedApplications();
    const filtered = existingApps.filter((a) => a.id !== appId);
    const updatedApps = [appItem, ...filtered];
    localStorage.setItem(STORAGE_KEY_APPS, JSON.stringify(updatedApps));

    const rawFindings = localStorage.getItem(STORAGE_KEY_FINDINGS);
    const allFindings: Record<string, FindingDetail[]> = rawFindings ? JSON.parse(rawFindings) : {};
    allFindings[appId] = [findingItem];
    localStorage.setItem(STORAGE_KEY_FINDINGS, JSON.stringify(allFindings));

    // Notify other components/tabs in real time
    window.dispatchEvent(new CustomEvent('reviewQueueUpdated', { detail: { appId, appItem } }));
  } catch (err) {
    console.error('Failed to save analysed application to storage', err);
  }

  return { app: appItem, finding: findingItem };
}
