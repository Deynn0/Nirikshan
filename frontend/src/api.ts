import { api as apiClient } from "./api/client";
import type { DemoAccount, DemoAccounts, Role, SessionInfo } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, message: string, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const SESSION_STORAGE_KEY = "nirikshan_session";
const LEGACY_AUTO_LOGIN_TOKEN = "offline-jwt-demo-token-12345";
const VALID_ROLES = new Set<Role>(["officer", "verifier", "admin", "institution"]);

interface StoredSession {
  token: string;
  username: string;
  role: "applicant" | "officer";
  appRole?: Role;
  displayName?: string;
  offline?: boolean;
}

let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export const VALID_USERNAMES = [
  "officer",
  "verifier",
  "admin",
  "inst1",
  "inst2",
  "inst3",
  "inst4",
  "inst5",
  "inst6",
  "inst7",
  "inst8",
  "inst9",
  "inst10",
  "inst11",
] as const;

export function isValidUsername(username: string): boolean {
  const norm = username.trim().toLowerCase();
  return (VALID_USERNAMES as readonly string[]).includes(norm);
}

function inferRole(username: string, roleHint?: Role): Role {
  if (roleHint && VALID_ROLES.has(roleHint)) return roleHint;
  const lower = username.toLowerCase().trim();
  if (lower.startsWith("inst") || lower === "applicant") {
    return "institution";
  }
  if (lower === "admin") return "admin";
  if (lower === "verifier") return "verifier";
  return "officer";
}

function toBackendRole(role: Role): "applicant" | "officer" {
  return role === "institution" ? "applicant" : "officer";
}

function notifySessionChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("nirikshan-session-changed"));
  }
}

function readStoredSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<StoredSession>;
    if (
      !parsed ||
      typeof parsed.token !== "string" ||
      !parsed.token ||
      parsed.token === LEGACY_AUTO_LOGIN_TOKEN ||
      typeof parsed.username !== "string" ||
      !parsed.username
    ) {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      return null;
    }
    const appRole = parsed.appRole && VALID_ROLES.has(parsed.appRole) ? parsed.appRole : undefined;
    const role: "applicant" | "officer" =
      parsed.role === "applicant" || parsed.role === "officer"
        ? parsed.role
        : appRole === "institution"
        ? "applicant"
        : "officer";
    return {
      token: parsed.token,
      username: parsed.username,
      role,
      appRole,
      displayName: typeof parsed.displayName === "string" ? parsed.displayName : undefined,
      offline: parsed.offline === true,
    };
  } catch {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

function writeStoredSession(session: StoredSession | null): void {
  if (session) {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    apiClient.setSession({
      token: session.token,
      username: session.username,
      role: session.role,
    });
  } else {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    apiClient.setSession(null);
  }
  notifySessionChanged();
}

export function hasStoredSession(): boolean {
  return readStoredSession() !== null;
}

function buildSessionInfo(saved: StoredSession): SessionInfo {
  const resolvedRole: Role =
    saved.appRole ?? (saved.role === "applicant" ? "institution" : "officer");
  return {
    csrf_token: saved.token,
    user: {
      id: `usr-${saved.username}`,
      username: saved.username,
      role: resolvedRole,
      display_name: saved.displayName || saved.username,
    },
  };
}

function isValidLocalJwt(token: string): boolean {
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  try {
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded)) as { exp?: unknown };
    return typeof payload.exp === "number" && payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

function parseMeResponse(data: unknown, saved: StoredSession): SessionInfo {
  if (!data || typeof data !== "object") {
    throw new ApiError(401, "Invalid session payload", null);
  }
  const obj = data as Record<string, unknown>;

  // Shape 1: { csrf_token, user: { id, username, role } }
  if (obj.user && typeof obj.user === "object") {
    const u = obj.user as Record<string, unknown>;
    if (typeof u.username === "string" && typeof u.role === "string" && VALID_ROLES.has(u.role as Role)) {
      return {
        csrf_token: typeof obj.csrf_token === "string" ? obj.csrf_token : saved.token,
        user: {
          id: typeof u.id === "string" ? u.id : `usr-${u.username}`,
          username: u.username,
          role: u.role as Role,
          display_name: typeof u.display_name === "string" ? u.display_name : u.username,
          institution_id: typeof u.institution_id === "string" ? u.institution_id : undefined,
        },
      };
    }
  }

  // Shape 2: Backend UserPrincipal { user_id, username, role, full_name, institution_id }
  if (typeof obj.user_id === "string" && typeof obj.username === "string" && typeof obj.role === "string") {
    // Reject the backend's unauthenticated default fallback principal
    if (obj.user_id === "usr-default-applicant") {
      throw new ApiError(401, "Not logged in", null);
    }
    const mappedRole: Role =
      saved.appRole ?? (obj.role === "applicant" ? "institution" : "officer");
    return {
      csrf_token: saved.token,
      user: {
        id: obj.user_id,
        username: obj.username,
        role: mappedRole,
        display_name:
          (typeof obj.full_name === "string" && obj.full_name) ||
          saved.displayName ||
          obj.username,
        institution_id: typeof obj.institution_id === "string" ? obj.institution_id : undefined,
      },
    };
  }

  throw new ApiError(401, "Invalid session payload", null);
}

export type Body = FormData | object | undefined;

const DEFAULT_DEMO: DemoAccounts = {
  accounts: [
    {
      id: "off-1",
      username: "officer",
      role: "officer",
      display_name: "Dr. Arvind Sharma (Scrutiny Officer)",
      role_label: "AICTE scrutiny officer",
    },
    {
      id: "ver-1",
      username: "verifier",
      role: "verifier",
      display_name: "S. K. Verma (Verification Cell)",
      role_label: "Verification cell",
    },
    {
      id: "adm-1",
      username: "admin",
      role: "admin",
      display_name: "Chief Auditor (Admin)",
      role_label: "Administrator / auditor",
    },
    {
      id: "inst-1",
      username: "inst1",
      role: "institution",
      institution: "Apex Institute of Technology & Management (A1)",
      display_name: "Apex Institute Registrar (A1)",
    },
    {
      id: "inst-2",
      username: "inst2",
      role: "institution",
      institution: "Trinity Polytechnic Institute (A2)",
      display_name: "Trinity Polytechnic Principal (A2)",
    },
    {
      id: "inst-3",
      username: "inst3",
      role: "institution",
      institution: "Pioneer College of Pharmacy (A3)",
      display_name: "Pioneer Pharmacy Dean (A3)",
    },
    {
      id: "inst-4",
      username: "inst4",
      role: "institution",
      institution: "Saraswati School of Management (A4)",
      display_name: "Saraswati Management Director (A4)",
    },
    {
      id: "inst-5",
      username: "inst5",
      role: "institution",
      institution: "Deccan College of Engineering & Research (A5)",
      display_name: "Deccan College Registrar (A5)",
    },
    {
      id: "inst-6",
      username: "inst6",
      role: "institution",
      institution: "Sterling Global Institute (A6)",
      display_name: "Sterling Global Director (A6)",
    },
    {
      id: "inst-7",
      username: "inst7",
      role: "institution",
      institution: "Vardhaman Institute of Technology (A7)",
      display_name: "Vardhaman Tech Dean (A7)",
    },
    {
      id: "inst-8",
      username: "inst8",
      role: "institution",
      institution: "National Institute of Engineering & Technology (A8)",
      display_name: "NIET Nanded Registrar (A8)",
    },
    {
      id: "inst-9",
      username: "inst9",
      role: "institution",
      institution: "Vidya Bharati Institute of Pharmaceutical Sciences (A9)",
      display_name: "Vidya Bharati Principal (A9)",
    },
    {
      id: "inst-10",
      username: "inst10",
      role: "institution",
      institution: "Rajiv Gandhi College of Computer Applications (A10)",
      display_name: "RGCCA Director (A10)",
    },
    {
      id: "inst-11",
      username: "inst11",
      role: "institution",
      institution: "K. J. Somaiya Polytechnic & Engineering Academy (A11)",
      display_name: "K.J. Somaiya Principal (A11)",
    },
  ],
  password: "demo-password",
  notice: "Valid usernames: officer, verifier, admin, or inst1 to inst11 (Applications A1 to A11)",
};

export async function request<T>(
  method: string,
  path: string,
  body?: Body,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", ...extraHeaders };
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (method !== "GET" && csrfToken) headers["x-csrf-token"] = csrfToken;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000); // 4 s timeout
    const res = await fetch(`/api${path}`, { method, headers, body: payload, credentials: "include", signal: controller.signal });
    clearTimeout(timeoutId);
    const text = await res.text();
    let data: unknown = undefined;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }
    if (!res.ok) {
      const detail = data && typeof data === "object" && "detail" in data ? (data as { detail: unknown }).detail : data;
      throw new ApiError(res.status, String(detail || res.statusText || "Request failed"), detail);
    }
    return data as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, "Backend unreachable, using offline mode", undefined);
  }
}

export const api = {
  login: async (username: string, password: string, roleHint?: Role): Promise<SessionInfo> => {
    const cleanUser = username.trim().toLowerCase();
    if (!isValidUsername(cleanUser)) {
      throw new ApiError(
        400,
        "Invalid username. Allowed logins are: 'officer', 'verifier', 'admin', or institution accounts 'inst1' through 'inst11'.",
        null
      );
    }
    const appRole = inferRole(cleanUser, roleHint);
    const backendRole = toBackendRole(appRole);
    const demoMatch = DEFAULT_DEMO.accounts.find((a) => a.username.toLowerCase() === cleanUser);
    const defaultDisplayName = demoMatch?.display_name || cleanUser;

    try {
      const res = await request<{
        access_token?: string;
        username?: string;
        role?: string;
      }>("POST", "/auth/token", {
        username: cleanUser,
        role: backendRole,
        password,
      });
      if (!res?.access_token) {
        throw new ApiError(500, "Invalid token response", res);
      }
      const resolvedUsername = res.username || cleanUser;
      const stored: StoredSession = {
        token: res.access_token,
        username: resolvedUsername,
        role: backendRole,
        appRole,
        displayName: defaultDisplayName,
        offline: false,
      };
      writeStoredSession(stored);
      return buildSessionInfo(stored);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 400 || err.status === 401 || err.status === 403 || err.status === 422)) {
        throw err;
      }
      // Fallback mock session for local / offline sandbox when backend is unreachable
      const stored: StoredSession = {
        token: `offline-session-${Date.now()}`,
        username: cleanUser,
        role: backendRole,
        appRole,
        displayName: defaultDisplayName,
        offline: true,
      };
      writeStoredSession(stored);
      return buildSessionInfo(stored);
    }
  },

  logout: async (): Promise<{ ok: boolean }> => {
    try {
      await request<{ ok: boolean }>("POST", "/auth/logout");
    } catch {
      // ignore
    }
    writeStoredSession(null);
    setCsrfToken(null);
    return { ok: true };
  },

  me: async (): Promise<SessionInfo> => {
    const saved = readStoredSession();
    if (!saved) {
      throw new ApiError(401, "Not logged in", null);
    }
    if (saved.offline && saved.token.startsWith("offline-session-")) {
      return buildSessionInfo(saved);
    }
    try {
      const data = await request<unknown>("GET", "/auth/me", undefined, {
        Authorization: `Bearer ${saved.token}`,
      });
      return parseMeResponse(data, saved);
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 0 || err.status >= 500) &&
        isValidLocalJwt(saved.token)
      ) {
        return buildSessionInfo(saved);
      }
      writeStoredSession(null);
      throw new ApiError(401, "Not logged in", null);
    }
  },

  demoAccounts: async (): Promise<DemoAccounts> => {
    try {
      const res = await request<DemoAccounts>("GET", "/auth/demo-accounts");
      if (res && Array.isArray(res.accounts)) {
        return res;
      }
      return DEFAULT_DEMO;
    } catch {
      return DEFAULT_DEMO;
    }
  },
};

export const qk = {
  me: ["me"] as const,
  demo: ["demo-accounts"] as const,
  dashboard: ["dashboard"] as const,
  applications: ["applications"] as const,
  application: (id: string) => ["application", id] as const,
};

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}
