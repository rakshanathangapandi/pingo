import { request } from './client';
import { DashboardOverview, DashboardStats, GiftStats, PaymentStats, RequestItem, UpcomingDeadlineItem } from '@/types';

export const getDashboardOverview = () => request<DashboardOverview>({ method: 'GET', url: '/dashboard/overview' });
export const getDashboardStats = () => request<DashboardStats>({ method: 'GET', url: '/dashboard/stats' });
export const getDashboardPendingRequests = (limit = 10) => request<RequestItem[]>({ method: 'GET', url: `/dashboard/pending-requests?limit=${limit}` });
export const getDashboardPaymentOverview = () => request<PaymentStats>({ method: 'GET', url: '/dashboard/payment-overview' });
export const getUpcomingDeadlines = (days = 7, limit = 10) => request<UpcomingDeadlineItem[]>({ method: 'GET', url: `/dashboard/upcoming-deadlines?days=${days}&limit=${limit}` });
export const getDashboardGiftDistribution = (limit = 10) => request<RequestItem[]>({ method: 'GET', url: `/dashboard/gift-distribution?limit=${limit}` });
export const getGiftStats = () => request<GiftStats>({ method: 'GET', url: '/gifts/stats' });
