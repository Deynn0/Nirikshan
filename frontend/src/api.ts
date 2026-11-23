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

let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
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

export async function request<T>(method: string, path: string, body?: Body): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (method !== "GET" && csrfToken) headers["x-csrf-token"] = csrfToken;

  try {
    const res = await fetch(`/api${path}`, { method, headers, body: payload, credentials: "include" });
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
  login: async (username: string, password: string): Promise<SessionInfo> => {
    try {
      const res = await request<SessionInfo>("POST", "/auth/login", { username, password });
      localStorage.setItem(
        "nirikshan_session",
        JSON.stringify({
          token: res.csrf_token || "mock-token",
          username: res.user.username,
          role: res.user.role === "institution" ? "applicant" : "officer",
        })
      );
      return res;
    } catch {
      // Fallback mock session for local / offline sandbox
      const role: Role =
        username.includes("inst") || username.includes("iit") || username.includes("bits") || username.includes("dtu") || username.includes("nit")
          ? "institution"
          : username.includes("admin")
          ? "admin"
          : username.includes("verifier")
          ? "verifier"
          : "officer";

      const session: SessionInfo = {
        csrf_token: `csrf-token-${Date.now()}`,
        user: {
          id: `usr-${username}`,
          username,
          role,
          display_name: username,
        },
      };
      localStorage.setItem(
        "nirikshan_session",
        JSON.stringify({
          token: session.csrf_token,
          username,
          role: role === "institution" ? "applicant" : "officer",
        })
      );
      return session;
    }
  },

  logout: async (): Promise<{ ok: boolean }> => {
    try {
      await request<{ ok: boolean }>("POST", "/auth/logout");
    } catch {
      // ignore
    }
    localStorage.removeItem("nirikshan_session");
    return { ok: true };
  },

  me: async (): Promise<SessionInfo> => {
    try {
      return await request<SessionInfo>("GET", "/auth/me");
    } catch {
      throw new ApiError(401, "Not logged in", null);
    }
  },

  demoAccounts: async (): Promise<DemoAccounts> => {
    try {
      return await request<DemoAccounts>("GET", "/auth/demo-accounts");
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
