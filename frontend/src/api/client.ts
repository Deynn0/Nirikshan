import type {
  AskWhyRequest,
  AskWhyResponse,
  Dossier,
  DossierCreate,
  FraudGraphResponse,
  HealthResponse,
  JobResponse,
  LoginRequest,
  ReportResponse,
  Rule,
  TokenResponse,
  UserSession,
} from './types';

const BASE_URL = '';

class ApiClient {
  private token: string | null = null;

  constructor() {
    const saved = localStorage.getItem('nirikshan_session');
    if (saved) {
      try {
        const session: UserSession = JSON.parse(saved);
        this.token = session.token;
      } catch (e) {
        console.error('Failed to parse saved session', e);
      }
    }
  }

  setSession(session: UserSession | null) {
    if (session) {
      this.token = session.token;
      localStorage.setItem('nirikshan_session', JSON.stringify(session));
    } else {
      this.token = null;
      localStorage.removeItem('nirikshan_session');
    }
  }

  getSession(): UserSession | null {
    const saved = localStorage.getItem('nirikshan_session');
    if (!saved) return null;
    try {
      return JSON.parse(saved);
    } catch {
      return null;
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    if (this.token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const data = await response.json();
        if (data && data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        }
      } catch {
        // ignore fallback
      }
      throw new Error(errorMsg);
    }

    return response.json() as Promise<T>;
  }

  // Auth
  async login(payload: LoginRequest): Promise<TokenResponse> {
    return this.request<TokenResponse>('/api/auth/token', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  // Dossiers
  async listDossiers(): Promise<Dossier[]> {
    return this.request<Dossier[]>('/api/dossiers');
  }

  async getDossier(dossierId: string): Promise<Dossier> {
    return this.request<Dossier>(`/api/dossiers/${dossierId}`);
  }

  async createDossier(payload: DossierCreate): Promise<Dossier> {
    return this.request<Dossier>('/api/dossiers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async verifyDossier(dossierId: string): Promise<Dossier> {
    return this.request<Dossier>(`/api/dossiers/${dossierId}/verify`, {
      method: 'POST',
    });
  }

  // Documents
  async uploadDocument(dossierId: string, formData: FormData): Promise<any> {
    return this.request<any>(`/api/dossiers/${dossierId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
  }

  getDocumentFileUrl(dossierId: string, documentId: string): string {
    return `${BASE_URL}/api/dossiers/${dossierId}/documents/${documentId}/file`;
  }

  // Jobs & SSE
  async submitEvaluationJob(dossierId: string): Promise<JobResponse> {
    return this.request<JobResponse>(`/api/jobs/dossiers/${dossierId}/evaluate`, {
      method: 'POST',
    });
  }

  async getJobStatus(jobId: string): Promise<JobResponse> {
    return this.request<JobResponse>(`/api/jobs/${jobId}`);
  }

  subscribeJobEvents(jobId: string, onMessage: (data: any) => void, onError?: (err: any) => void): () => void {
    const eventSource = new EventSource(`${BASE_URL}/api/jobs/${jobId}/events`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        // SSE raw or comment
      }
    };

    eventSource.onerror = (err) => {
      if (onError) onError(err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }

  // Reports
  async getReport(dossierId: string): Promise<ReportResponse> {
    return this.request<ReportResponse>(`/api/dossiers/${dossierId}/report`);
  }

  // Fraud Graph & Findings
  async getFraudGraph(): Promise<FraudGraphResponse> {
    return this.request<FraudGraphResponse>('/api/fraud/graph');
  }

  async getFraudFindings(): Promise<any[]> {
    return this.request<any[]>('/api/fraud/findings');
  }

  // Advisory Ask Why
  async askWhy(payload: AskWhyRequest): Promise<AskWhyResponse> {
    return this.request<AskWhyResponse>('/api/advisory/ask-why', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Rules
  async listRules(): Promise<Rule[]> {
    return this.request<Rule[]>('/api/rules');
  }
}

export const api = new ApiClient();
