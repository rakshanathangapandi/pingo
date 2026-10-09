import { format, parseISO } from 'date-fns';
import { PaymentStatus, ReminderPriority, RequestStatus, GiftStatus, AssetStatus } from '@/types';

export function formatDate(value?: string | null) {
  if (!value) return '—';
  try {
    return format(parseISO(value), 'MMM d, yyyy');
  } catch {
    return value;
  }
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);
}

export function formatStatus(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function priorityTone(priority?: ReminderPriority) {
  switch (priority) {
    case 'low': return 'success';
    case 'medium': return 'info';
    case 'high':
    case 'urgent': return 'warning';
    default: return 'neutral';
  }
}

export function paymentTone(status?: PaymentStatus) {
  switch (status) {
    case 'paid': return 'success';
    case 'due_soon': return 'warning';
    case 'overdue': return 'danger';
    case 'cancelled': return 'neutral';
    default: return 'info';
  }
}

export function requestTone(status?: RequestStatus) {
  switch (status) {
    case 'approved':
    case 'completed': return 'success';
    case 'rejected':
    case 'cancelled': return 'danger';
    case 'under_review': return 'warning';
    default: return 'info';
  }
}

export function giftTone(status?: GiftStatus) {
  switch (status) {
    case 'delivered': return 'success';
    case 'in_progress': return 'info';
    case 'cancelled': return 'danger';
    default: return 'warning';
  }
}

export function assetTone(status?: AssetStatus) {
  switch (status) {
    case 'assigned': return 'info';
    case 'available': return 'success';
    case 'in_maintenance': return 'warning';
    default: return 'danger';
  }
}
