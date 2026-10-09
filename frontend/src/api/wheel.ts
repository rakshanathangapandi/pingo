import { request } from './client';
import { PaginatedResponse, WheelEntry, WheelSpin } from '@/types';

export const listWheelEntries = (activeOnly = true) => request<WheelEntry[]>({ method: 'GET', url: `/wheel/entries?active_only=${activeOnly}` });
export const createWheelEntry = (data: Record<string, unknown>) => request<WheelEntry>({ method: 'POST', url: '/wheel/entries', data });
export const updateWheelEntry = (id: number, data: Record<string, unknown>) => request<WheelEntry>({ method: 'PATCH', url: `/wheel/entries/${id}`, data });
export const deleteWheelEntry = (id: number) => request<void>({ method: 'DELETE', url: `/wheel/entries/${id}` });
export const spinWheel = () => request<WheelSpin>({ method: 'POST', url: '/wheel/spin' });
export const listWheelSpins = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<WheelSpin>>({ method: 'GET', url: `/wheel/spins?${query.toString()}` });
};
