import { request } from './client';
import { PaginatedResponse, RequestItem } from '@/types';

export const listRequests = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<RequestItem>>({ method: 'GET', url: `/requests/?${query.toString()}` });
};
export const getRequest = (id: number) => request<RequestItem>({ method: 'GET', url: `/requests/${id}` });
export const createRequest = (data: Record<string, unknown>) => request<RequestItem>({ method: 'POST', url: '/requests/', data });
export const updateRequest = (id: number, data: Record<string, unknown>) => request<RequestItem>({ method: 'PATCH', url: `/requests/${id}`, data });
export const approveRequest = (id: number, notes?: string) => request<RequestItem>({ method: 'POST', url: `/requests/${id}/approve`, params: notes ? { notes } : {} });
export const rejectRequest = (id: number, notes: string) => request<RequestItem>({ method: 'POST', url: `/requests/${id}/reject`, params: { notes } });
export const completeRequest = (id: number, notes?: string) => request<RequestItem>({ method: 'POST', url: `/requests/${id}/complete`, params: notes ? { notes } : {} });
export const deleteRequest = (id: number) => request<void>({ method: 'DELETE', url: `/requests/${id}` });
