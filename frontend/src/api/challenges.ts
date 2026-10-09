import { request } from './client';
import { PaginatedResponse, SundayChallenge } from '@/types';

export const listChallenges = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<SundayChallenge>>({ method: 'GET', url: `/challenges/?${query.toString()}` });
};
export const getCurrentChallenge = () => request<SundayChallenge | null>({ method: 'GET', url: '/challenges/current' });
export const createChallenge = (data: Record<string, unknown>) => request<SundayChallenge>({ method: 'POST', url: '/challenges/', data });
export const updateChallenge = (id: number, data: Record<string, unknown>) => request<SundayChallenge>({ method: 'PATCH', url: `/challenges/${id}`, data });
export const participateInChallenge = (id: number) => request<unknown>({ method: 'POST', url: `/challenges/${id}/participate` });
export const completeChallenge = (id: number, notes?: string) => request<unknown>({ method: 'POST', url: `/challenges/${id}/complete`, params: notes ? { submission_notes: notes } : {} });
