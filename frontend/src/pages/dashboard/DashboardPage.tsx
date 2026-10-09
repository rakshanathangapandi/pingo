import { ArrowRight, Banknote, CalendarClock, CircleDollarSign, Gift, PackageCheck, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardOverview } from '@/api/dashboard';
import { LoadingState } from '@/components/common/LoadingState';
import { StatusBadge } from '@/components/common/StatusBadge';
import { useApi } from '@/hooks/useApi';
import { formatCurrency, formatDate, formatStatus, priorityTone } from '@/utils/formatters';
import { DashboardOverview } from '@/types';

const metrics = [
  { key: 'pending_requests', label: 'Pending Requests', icon: ShieldCheck, color: 'sky' },
  { key: 'pending_payments', label: 'Pending Payments', icon: Banknote, color: 'amber' },
  { key: 'overdue_payments', label: 'Overdue Payments', icon: CircleDollarSign, color: 'rose' },
  { key: 'upcoming_deadlines', label: 'Upcoming Deadlines', icon: CalendarClock, color: 'violet' },
  { key: 'total_assets', label: 'Company Assets', icon: PackageCheck, color: 'emerald' },
  { key: 'gifts_assigned', label: 'Gifts Assigned', icon: Gift, color: 'orange' },
  { key: 'gifts_in_progress', label: 'Gifts In Progress', icon: Gift, color: 'blue' },
  { key: 'gifts_delivered', label: 'Gifts Delivered', icon: Gift, color: 'green' },
] as const;

const getMetricValue = (value: number | undefined) => value ?? 0;

export function DashboardPage() {
  const { data, error, isLoading } = useApi<DashboardOverview>(() => getDashboardOverview());

  if (isLoading) return <LoadingState message="Loading dashboard..." />;
  if (error || !data) return <div className="card p-6 text-sm text-rose-600">{error || 'Unable to load dashboard.'}</div>;

  const { stats, upcoming_deadlines, pending_requests, payment_overview, gift_distribution } = data;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Overview</p>
          <h1 className="page-title">Admin Management Dashboard</h1>
        </div>
        <Link to="/requests" className="inline-flex items-center gap-2 self-start rounded-xl bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700">
          Review requests <ArrowRight className="h-4 w-4" />
        </Link>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map(({ key, label, icon: Icon, color }) => (
          <div key={key} className="card p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-bold text-slate-900">{getMetricValue(stats[key])}</p>
              </div>
              <span className={`rounded-xl bg-${color}-100 p-3 text-${color}-600`}>
                <Icon className="h-5 w-5" />
              </span>
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Upcoming deadlines</h2>
            <Link className="text-sm font-semibold text-primary-600" to="/reminders">View all</Link>
          </div>
          <div className="space-y-3">
            {upcoming_deadlines.length ? upcoming_deadlines.map((item) => (
              <div key={`${item.type}-${item.id}`} className="flex items-center justify-between rounded-xl border border-slate-200 p-3">
                <div>
                  <p className="font-medium text-slate-800">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{item.type} • {formatDate(item.deadline)}</p>
                </div>
                <StatusBadge tone={priorityTone(item.priority)}>{item.priority}</StatusBadge>
              </div>
            )) : <p className="text-sm text-slate-500">No upcoming deadlines.</p>}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Sunday challenge</h2>
            <Link className="text-sm font-semibold text-primary-600" to="/challenges">Manage</Link>
          </div>
          {stats.active_challenge ? (
            <div className="space-y-3">
              <div className="rounded-xl bg-primary-50 p-4">
                <p className="font-semibold text-primary-900">{stats.active_challenge.title}</p>
                <p className="mt-1 text-sm text-slate-600">{stats.active_challenge.description || 'No description provided.'}</p>
              </div>
              <p className="text-sm text-slate-500">Challenge date: {formatDate(stats.active_challenge.challenge_date)}</p>
            </div>
          ) : <p className="text-sm text-slate-500">No active challenge configured.</p>}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Pending requests</h2>
            <Link className="text-sm font-semibold text-primary-600" to="/requests">Review all</Link>
          </div>
          <div className="space-y-3">
            {pending_requests.length ? pending_requests.map((request) => (
              <div key={request.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 p-3">
                <div>
                  <p className="font-medium text-slate-800">{request.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{request.request_id} • {formatDate(request.due_date || request.requested_date)}</p>
                </div>
                <StatusBadge tone={priorityTone(request.priority)}>{formatStatus(request.status)}</StatusBadge>
              </div>
            )) : <p className="text-sm text-slate-500">No requests currently require admin action.</p>}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Payment overview</h2>
            <Link className="text-sm font-semibold text-primary-600" to="/payments">Open payments</Link>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-slate-500">Pending</p><p className="mt-1 font-semibold">{payment_overview.total_pending}</p></div>
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-slate-500">Due soon</p><p className="mt-1 font-semibold">{payment_overview.total_due_soon}</p></div>
            <div className="rounded-xl bg-rose-50 p-3"><p className="text-rose-600">Overdue</p><p className="mt-1 font-semibold">{payment_overview.total_overdue}</p></div>
            <div className="rounded-xl bg-emerald-50 p-3"><p className="text-emerald-600">Paid</p><p className="mt-1 font-semibold">{payment_overview.total_paid}</p></div>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <p className="flex justify-between"><span>Amount pending</span><strong>{formatCurrency(payment_overview.amount_pending)}</strong></p>
            <p className="flex justify-between"><span>Amount paid</span><strong>{formatCurrency(payment_overview.amount_paid)}</strong></p>
            <p className="flex justify-between"><span>Overdue amount</span><strong>{formatCurrency(payment_overview.amount_overdue)}</strong></p>
          </div>
        </div>
      </section>

      <section className="card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Gift distribution</h2>
          <Link className="text-sm font-semibold text-primary-600" to="/gifts">Manage gifts</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-500"><tr><th className="pb-3 pr-4 font-semibold">Gift</th><th className="pb-3 pr-4 font-semibold">Recipient</th><th className="pb-3 pr-4 font-semibold">Status</th><th className="pb-3 font-semibold">Expected delivery</th></tr></thead>
            <tbody>
              {gift_distribution.length ? gift_distribution.map((gift) => (
                <tr key={gift.id} className="border-t border-slate-200">
                  <td className="py-3 pr-4 font-medium text-slate-800">{gift.name}</td>
                  <td className="py-3 pr-4 text-slate-600">{gift.recipient?.full_name || gift.recipient?.email || 'Unassigned'}</td>
                  <td className="py-3 pr-4"><StatusBadge tone={gift.status === 'delivered' ? 'success' : gift.status === 'in_progress' ? 'info' : 'warning'}>{formatStatus(gift.status)}</StatusBadge></td>
                  <td className="py-3">{gift.expected_delivery_date ? formatDate(gift.expected_delivery_date) : '—'}</td>
                </tr>
              )) : <tr><td className="py-6 text-sm text-slate-500" colSpan={4}>No gifts to display.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
