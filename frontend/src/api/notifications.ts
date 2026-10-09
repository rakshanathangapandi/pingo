import { request } from './client';
import { Notification, PaginatedResponse } from '@/types';

export const listNotifications = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<Notification>>({ method: 'GET', url: `/notifications/?${query.toString()}` });
};
export const markNotificationRead = (id: number) => request<Notification>({ method: 'POST', url: `/notifications/${id}/read` });
export const markAllNotificationsRead = () => request<void>({ method: 'POST', url: '/notifications/read-all' });
