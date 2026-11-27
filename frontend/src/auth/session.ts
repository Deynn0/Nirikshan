import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, api, hasStoredSession, qk, setCsrfToken } from "../api";
import type { Role, SessionInfo } from "../types";

async function loadSession(): Promise<SessionInfo | null> {
  try {
    const s = await api.me();
    if (!s?.user?.role) {
      setCsrfToken(null);
      return null;
    }
    setCsrfToken(s.csrf_token);
    return s;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      setCsrfToken(null);
      return null;
    }
    return null;
  }
}

export function useSession() {
  return useQuery({
    queryKey: qk.me,
    queryFn: loadSession,
    staleTime: Infinity,
    retry: false,
    initialData: () => (hasStoredSession() ? undefined : null),
  });
}

/** The signed-in session; only call below a guard that has already resolved it. */
export function useAuth() {
  const { data } = useSession();
  const role = data?.user?.role;
  return {
    session: data ?? null,
    user: data?.user ?? null,
    role,
    is: (...roles: Role[]) => !!role && roles.includes(role),
  };
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password, role }: { username: string; password: string; role?: Role }) =>
      api.login(username, password, role),
    onSuccess: (s) => {
      setCsrfToken(s.csrf_token);
      qc.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" && q.queryKey[0] !== "demo-accounts" });
      qc.setQueryData(qk.me, s);
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.logout(),
    onSettled: () => {
      setCsrfToken(null);
      qc.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" && q.queryKey[0] !== "demo-accounts" });
      qc.setQueryData(qk.me, null);
    },
  });
}

export function homePath(role: Role | undefined): string {
  return role === "institution" ? "/applicant" : "/workspace/queue";
}
