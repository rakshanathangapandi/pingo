import { useEffect, useState } from 'react';
import { CheckCheck, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { request } from '@/api/client';
import { listNotifications, markAllNotificationsRead, markNotificationRead } from '@/api/notifications';
import { DataTable } from '@/components/common/DataTable';
import { LoadingState } from '@/components/common/LoadingState';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Notification, PaginatedResponse } from '@/types';
import { formatDate, formatStatus } from '@/utils/formatters';

export function NotificationsPage() {
  const [data, setData] = useState<PaginatedResponse<Notification> | null>(null); const [loading, setLoading] = useState(true);
  const load = async (page = 1) => { setLoading(true); try { setData(await listNotifications({ page, page_size: 10 })); } catch (error) { toast.error(error instanceof Error ? error.message : 'Unable to load notifications.'); } finally { setLoading(false); } };
  useEffect(() => { void load(1); }, []);
  const markRead = async (notification: Notification) => { try { await markNotificationRead(notification.id); toast.success('Notification marked as read'); await load(); } catch (error) { toast.error(error instanceof Error ? error.message : 'Unable to update notification.'); } };
  const deleteNotification = async (id: number) => { try { await request<void>({ method: 'DELETE', url: `/notifications/${id}` }); toast.success('Notification deleted'); await load(); } catch (error) { toast.error(error instanceof Error ? error.message : 'Unable to delete notification.'); } };
  const markAllRead = async () => { try { await markAllNotificationsRead(); toast.success('All notifications marked as read'); await load(); } catch (error) { toast.error(error instanceof Error ? error.message : 'Unable to update notifications.'); } };
  return <div className="space-y-6"><header className="flex items-center justify-between"><div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Communications</p><h1 className="page-title">Notifications</h1></div><button type="button" onClick={() => void markAllRead()} className="button-secondary"><CheckCheck className="mr-2 h-4 w-4" />Mark all read</button></header>
    <section className="card p-5">{data ? <DataTable columns={[{ key: 'title', label: 'Notification', render: (row) => <><div className="font-medium text-slate-800">{row.title}</div><div className="mt-1 text-xs text-slate-500">{row.message}</div></> }, { key: 'type', label: 'Type', render: (row) => <StatusBadge>{formatStatus(row.notification_type)}</StatusBadge> }, { key: 'date', label: 'Date', render: (row) => formatDate(row.created_at) }, { key: 'status', label: 'Status', render: (row) => <StatusBadge tone={row.is_read ? 'success' : 'warning'}>{row.is_read ? 'Read' : 'Unread'}</StatusBadge> }, { key: 'actions', label: 'Actions', render: (row) => <div className="flex gap-2"><button type="button" disabled={row.is_read} onClick={() => void markRead(row)} className="rounded-lg bg-sky-100 px-2.5 py-1.5 text-xs font-semibold text-sky-700 disabled:opacity-40">Mark read</button><button type="button" onClick={() => void deleteNotification(row.id)} className="rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700"><Trash2 className="mr-1 inline h-3.5 w-3.5" />Delete</button></div> }]} data={data.items} loading={loading} emptyTitle="No notifications" emptyDescription="You will see platform updates here." page={data.page} totalPages={data.total_pages} onPageChange={(nextPage) => void load(nextPage)} /> : <LoadingState message="Loading notifications..." />}</section></div>;
}
