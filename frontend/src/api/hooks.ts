import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { AskWhyRequest, DossierCreate } from './types';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30000,
  });
}

export function useDossiers() {
  return useQuery({
    queryKey: ['dossiers'],
    queryFn: () => api.listDossiers(),
  });
}

export function useDossier(dossierId: string | undefined) {
  return useQuery({
    queryKey: ['dossier', dossierId],
    queryFn: () => (dossierId ? api.getDossier(dossierId) : null),
    enabled: !!dossierId,
  });
}

export function useCreateDossier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DossierCreate) => api.createDossier(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dossiers'] });
    },
  });
}

export function useVerifyDossier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dossierId: string) => api.verifyDossier(dossierId),
    onSuccess: (data, dossierId) => {
      queryClient.invalidateQueries({ queryKey: ['dossiers'] });
      queryClient.invalidateQueries({ queryKey: ['dossier', dossierId] });
      queryClient.invalidateQueries({ queryKey: ['report', dossierId] });
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dossierId, formData }: { dossierId: string; formData: FormData }) =>
      api.uploadDocument(dossierId, formData),
    onSuccess: (_, { dossierId }) => {
      queryClient.invalidateQueries({ queryKey: ['dossier', dossierId] });
    },
  });
}

export function useSubmitJob() {
  return useMutation({
    mutationFn: (dossierId: string) => api.submitEvaluationJob(dossierId),
  });
}

export function useJobStatus(jobId: string | undefined) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => (jobId ? api.getJobStatus(jobId) : null),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'COMPLETED' || status === 'FAILED' ? false : 1500;
    },
  });
}

export function useReport(dossierId: string | undefined) {
  return useQuery({
    queryKey: ['report', dossierId],
    queryFn: () => (dossierId ? api.getReport(dossierId) : null),
    enabled: !!dossierId,
  });
}

export function useFraudGraph() {
  return useQuery({
    queryKey: ['fraudGraph'],
    queryFn: () => api.getFraudGraph(),
  });
}

export function useFraudFindings() {
  return useQuery({
    queryKey: ['fraudFindings'],
    queryFn: () => api.getFraudFindings(),
  });
}

export function useRules() {
  return useQuery({
    queryKey: ['rules'],
    queryFn: () => api.listRules(),
  });
}

export function useAskWhy() {
  return useMutation({
    mutationFn: (payload: AskWhyRequest) => api.askWhy(payload),
  });
}
