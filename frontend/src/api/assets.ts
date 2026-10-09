import { request } from './client';
import { Asset, PaginatedResponse } from '@/types';

export const listAssets = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<Asset>>({ method: 'GET', url: `/assets/?${query.toString()}` });
};
export const createAsset = (data: Record<string, unknown>) => request<Asset>({ method: 'POST', url: '/assets/', data });
export const updateAsset = (id: number, data: Record<string, unknown>) => request<Asset>({ method: 'PATCH', url: `/assets/${id}`, data });
export const assignAsset = (id: number, assigneeId: number) => request<Asset>({ method: 'POST', url: `/assets/${id}/assign`, params: { assignee_id: assigneeId } });
export const returnAsset = (id: number) => request<Asset>({ method: 'POST', url: `/assets/${id}/return` });
export const deleteAsset = (id: number) => request<void>({ method: 'DELETE', url: `/assets/${id}` });
