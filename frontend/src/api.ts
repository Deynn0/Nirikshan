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

function inferRole(username: string, roleHint?: Role): Role {
  if (roleHint && VALID_ROLES.has(roleHint)) return roleHint;
  const lower = username.toLowerCase();
  if (
    lower.includes("inst") ||
    lower.includes("iit") ||
    lower.includes("bits") ||
    lower.includes("dtu") ||
    lower.includes("nit")
  ) {
    return "institution";
  }
  if (lower.includes("admin")) return "admin";
  if (lower.includes("verifier")) return "verifier";
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
      role_label: "Scrutiny officer",
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
      role_label: "Administrator and auditor",
    },
    {
      id: "inst-1",
      username: "iitdelhi",
      role: "institution",
      institution: "IIT Delhi",
      display_name: "Prof. R. Mehta (Registrar)",
    },
    {
      id: "inst-2",
      username: "bitspilani",
      role: "institution",
      institution: "BITS Pilani",
      display_name: "Col. S. Rao (Director)",
    },
    {
      id: "inst-3",
      username: "nittrichy",
      role: "institution",
      institution: "NIT Trichy",
      display_name: "Dr. K. Swaminathan (Dean)",
    },
    {
      id: "inst-4",
      username: "dtu",
      role: "institution",
      institution: "Delhi Technological University",
      display_name: "Dr. P. Bansal (Registrar)",
    },
    {
      id: "inst-5",
      username: "iitbombay",
      role: "institution",
      institution: "IIT Bombay",
      display_name: "Prof. S. Joshi (Registrar)",
    },
  ],
  password: "demo-password",
  notice: "Pre-configured synthetic profiles for regulatory testing",
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
    const appRole = inferRole(username, roleHint);
    const backendRole = toBackendRole(appRole);
    try {
      const res = await request<{
        access_token?: string;
        username?: string;
        role?: string;
      }>("POST", "/auth/token", {
        username,
        role: backendRole,
        password,
      });
      if (!res?.access_token) {
        throw new ApiError(500, "Invalid token response", res);
      }
      const resolvedUsername = res.username || username;
      const stored: StoredSession = {
        token: res.access_token,
        username: resolvedUsername,
        role: backendRole,
        appRole,
        displayName: resolvedUsername,
        offline: false,
      };
      writeStoredSession(stored);
      return buildSessionInfo(stored);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403 || err.status === 422)) {
        throw err;
      }
      // Fallback mock session for local / offline sandbox when backend is unreachable
      const stored: StoredSession = {
        token: `offline-session-${Date.now()}`,
        username,
        role: backendRole,
        appRole,
        displayName: username,
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
