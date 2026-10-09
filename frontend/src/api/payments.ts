import { request } from './client';
import { PaginatedResponse, Payment, PaymentStats } from '@/types';

export const listPayments = (params: Record<string, string | number | undefined> = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  return request<PaginatedResponse<Payment>>({ method: 'GET', url: `/payments/?${query.toString()}` });
};
export const createPayment = (data: Record<string, unknown>) => request<Payment>({ method: 'POST', url: '/payments/', data });
export const updatePayment = (id: number, data: Record<string, unknown>) => request<Payment>({ method: 'PATCH', url: `/payments/${id}`, data });
export const markPaymentPaid = (id: number, method: string, reference?: string, notes?: string) => request<Payment>({ method: 'POST', url: `/payments/${id}/mark-paid`, params: { payment_method: method, payment_reference: reference, notes } });
export const deletePayment = (id: number) => request<void>({ method: 'DELETE', url: `/payments/${id}` });
export const getPaymentStats = () => request<PaymentStats>({ method: 'GET', url: '/payments/stats' });
