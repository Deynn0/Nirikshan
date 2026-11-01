import type { paths } from './schema';

export type HealthResponse = paths['/api/health']['get']['responses']['200']['content']['application/json'];
export type TokenResponse = paths['/api/auth/token']['post']['responses']['200']['content']['application/json'];
export type LoginRequest = paths['/api/auth/token']['post']['requestBody']['content']['application/json'];

export type Dossier = paths['/api/dossiers/{dossier_id}']['get']['responses']['200']['content']['application/json'];
export type DossierList = paths['/api/dossiers']['get']['responses']['200']['content']['application/json'];
export type DossierCreate = paths['/api/dossiers']['post']['requestBody']['content']['application/json'];

export type DocumentRecord = Dossier['documents'][number];
export type Finding = Dossier['findings'][number];

export type JobResponse = paths['/api/jobs/{job_id}']['get']['responses']['200']['content']['application/json'];
export type ReportResponse = paths['/api/dossiers/{dossier_id}/report']['get']['responses']['200']['content']['application/json'];

export type FraudGraphResponse = paths['/api/fraud/graph']['get']['responses']['200']['content']['application/json'];

export type AskWhyRequest = paths['/api/advisory/ask-why']['post']['requestBody']['content']['application/json'];
export type AskWhyResponse = paths['/api/advisory/ask-why']['post']['responses']['200']['content']['application/json'];

export type Rule = paths['/api/rules']['get']['responses']['200']['content']['application/json'][number];

export type UserRole = 'applicant' | 'officer' | 'admin' | 'scrutiny_officer';

export interface UserSession {
  token: string;
  username: string;
  role: 'applicant' | 'officer';
  institutionId?: string;
}

export interface RectificationItem {
  id: string;
  findingId: string;
  ruleId: string;
  deficiencyText: string;
  applicantResponse: string;
  documentRef?: string;
  timestamp: string;
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED';
}
