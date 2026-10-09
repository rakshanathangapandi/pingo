import { request } from './client';
import { Gift, PaginatedResponse } from '@/types';

export const listGifts = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<Gift>>({ method: 'GET', url: `/gifts/?${query.toString()}` });
};
export const createGift = (data: Record<string, unknown>) => request<Gift>({ method: 'POST', url: '/gifts/', data });
export const updateGift = (id: number, data: Record<string, unknown>) => request<Gift>({ method: 'PATCH', url: `/gifts/${id}`, data });
export const markGiftDelivered = (id: number) => request<Gift>({ method: 'POST', url: `/gifts/${id}/deliver` });
export const deleteGift = (id: number) => request<void>({ method: 'DELETE', url: `/gifts/${id}` });
