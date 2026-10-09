import { request } from './client';
import { PaginatedResponse, Reminder } from '@/types';

export const listReminders = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<Reminder>>({ method: 'GET', url: `/reminders/?${query.toString()}` });
};
export const createReminder = (data: Record<string, unknown>) => request<Reminder>({ method: 'POST', url: '/reminders/', data });
export const updateReminder = (id: number, data: Record<string, unknown>) => request<Reminder>({ method: 'PATCH', url: `/reminders/${id}`, data });
export const completeReminder = (id: number) => request<Reminder>({ method: 'POST', url: `/reminders/${id}/complete` });
export const deleteReminder = (id: number) => request<void>({ method: 'DELETE', url: `/reminders/${id}` });
export const autoCollectReminders = () => request<{ message: string; counts: Record<string, number> }>({ method: 'POST', url: '/reminders/auto-collect' });
