export type Role = "officer" | "verifier" | "admin" | "institution";

export * from "./landing/hero/eyeState";

export interface DemoAccount {
  id: string;
  username: string;
  role: Role;
  display_name: string;
  role_label?: string;
  institution?: string;
}

export interface DemoAccounts {
  accounts: DemoAccount[];
  password: string;
  notice: string;
}

export interface SessionInfo {
  csrf_token: string | null;
  user: {
    id: string;
    username: string;
    role: Role;
    display_name?: string;
    institution_id?: string;
  };
}

export type ActiveRuleset = unknown;
export type Application = unknown;
export type ApplicationDetail = unknown;
export type AuditEvent = unknown;
export type CampusPayload = unknown;
export type ChainVerification = unknown;
export type Checkpoint = unknown;
export type Dashboard = unknown;
export type Declared = unknown;
export type DocumentDetail = unknown;
export type DocumentSummary = unknown;
export type Finding = unknown;
export type Institution = unknown;
export type NewApplicationBody = unknown;
export type PdfVerifyResult = unknown;
export type PlatformStatus = unknown;
export type QueuedRun = unknown;
export type RectificationItem = unknown;
export type ReplayResult = unknown;
export type RetentionPlan = unknown;
export type ReviewAction = unknown;
export type ReviewEntry = unknown;
export type RuleImpact = unknown;
export type RunBrief = unknown;
export type RunFull = unknown;
export type RunMetrics = unknown;
export type RunProgress = unknown;
export type SimIssuer = unknown;
export type SimLookup = unknown;
export type VerificationAttempt = unknown;
