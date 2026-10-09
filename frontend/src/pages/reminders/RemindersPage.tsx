import { useMemo, useState } from 'react';
import { CalendarPlus, CheckCircle2, Filter, RefreshCw, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { createReminder, deleteReminder, listReminders, completeReminder, autoCollectReminders } from '@/api/reminders';
import { DataTable } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { LoadingState } from '@/components/common/LoadingState';
import { StatusBadge } from '@/components/common/StatusBadge';
import { PaginatedResponse, Reminder, ReminderStatus } from '@/types';
import { formatDate, formatStatus, priorityTone } from '@/utils/formatters';

const emptyForm = {
  title: '',
  description: '',
  deadline: '',
  deadline_time: '',
  priority: 'medium',
  reminder_schedule: '1 day before',
  assignee_id: '',
};

export function RemindersPage() {
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState<ReminderStatus | 'all'>('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<Reminder> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async (nextPage = page) => {
    setLoading(true);
    setError('');
    try {
      const response = await listReminders({ page: nextPage, page_size: 10, search: search || undefined, status: status === 'all' ? undefined : status });
      setData(response);
      setPage(nextPage);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to load reminders.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await createReminder({
        ...form,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : undefined,
        reminder_schedule: form.reminder_schedule ? [form.reminder_schedule] : [],
      });
      toast.success('Reminder created');
      setForm(emptyForm);
      await load(1);
    } catch (caughtError) {
      toast.error(caughtError instanceof Error ? caughtError.message : 'Unable to create reminder.');
    }
  };

  const handleComplete = async (id: number) => {
    try {
      await completeReminder(id);
      toast.success('Reminder completed');
      await load();
    } catch (caughtError) {
      toast.error(caughtError instanceof Error ? caughtError.message : 'Unable to complete reminder.');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteReminder(id);
      toast.success('Reminder deleted');
      await load();
    } catch (caughtError) {
      toast.error(caughtError instanceof Error ? caughtError.message : 'Unable to delete reminder.');
    }
  };

  const handleAutoCollect = async () => {
    try {
      const result = await autoCollectReminders();
      toast.success(result.message);
      await load(1);
    } catch (caughtError) {
      toast.error(caughtError instanceof Error ? caughtError.message : 'Unable to auto-collect reminders.');
    }
  };

  const filters = useMemo(() => (
    <div className="flex flex-wrap items-center gap-3">
      <input className="input max-w-xs" placeholder="Search title or description" value={search} onChange={(event) => setSearch(event.target.value)} />
      <select className="input max-w-[180px]" value={status} onChange={(event) => setStatus(event.target.value as ReminderStatus | 'all')}>
        <option value="all">All statuses</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
      </select>
      <button type="button" onClick={() => void load(1)} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"><Filter className="mr-2 inline h-4 w-4" />Apply</button>
      <button type="button" onClick={() => void handleAutoCollect()} className="inline-flex items-center rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"><RefreshCw className="mr-2 inline h-4 w-4" />Auto-collect</button>
    </div>
  ), [search, status, load]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Planning</p>
          <h1 className="page-title">Reminder & deadline management</h1>
        </div>
      </header>

      <section className="card p-5">
        <div className="mb-5 flex items-center gap-2"><CalendarPlus className="h-5 w-5 text-primary-600" /><h2 className="font-semibold text-slate-900">Create reminder</h2></div>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
          <div className="md:col-span-2"><label className="label">Title<input className="input" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label></div>
          <div className="md:col-span-2"><label className="label">Description<textarea className="input min-h-24 resize-y" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label></div>
          <div><label className="label">Deadline<input type="date" className="input" required value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} /></label></div>
          <div><label className="label">Time<input type="time" className="input" value={form.deadline_time} onChange={(event) => setForm({ ...form, deadline_time: event.target.value })} /></label></div>
          <div><label className="label">Priority<select className="input" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label></div>
          <div><label className="label">Assigned person ID<input type="number" className="input" value={form.assignee_id} onChange={(event) => setForm({ ...form, assignee_id: event.target.value })} /></label></div>
          <div className="md:col-span-2"><label className="label">Reminder schedule<input className="input" placeholder="Example: 3 days before" value={form.reminder_schedule} onChange={(event) => setForm({ ...form, reminder_schedule: event.target.value })} /></label></div>
          <div className="md:col-span-2"><button type="submit" className="rounded-xl bg-primary-600 px-5 py-2.5 font-semibold text-white hover:bg-primary-700">Create reminder</button></div>
        </form>
      </section>

      <section className="card p-5">
        {filters}
        {error ? <div className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}
        {!loading && data ? (
          <div className="mt-5">
            <DataTable
              columns={[
                { key: 'title', label: 'Title', render: (row) => <><div className="font-medium text-slate-800">{row.title}</div><div className="mt-1 text-xs text-slate-500">{row.description || 'No description'}</div></> },
                { key: 'deadline', label: 'Deadline', render: (row) => <span>{formatDate(row.deadline)}</span> },
                { key: 'priority', label: 'Priority', render: (row) => <StatusBadge tone={priorityTone(row.priority)}>{formatStatus(row.priority)}</StatusBadge> },
                { key: 'status', label: 'Status', render: (row) => <StatusBadge tone={row.status === 'completed' ? 'success' : 'warning'}>{formatStatus(row.status)}</StatusBadge> },
                { key: 'assignee', label: 'Assigned', render: (row) => row.assignee?.full_name || row.assignee?.email || 'Unassigned' },
                { key: 'actions', label: 'Actions', render: (row) => <div className="flex gap-2"><button type="button" onClick={() => void handleComplete(row.id)} disabled={row.status === 'completed'} className="rounded-lg bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"><CheckCircle2 className="mr-1 inline h-3.5 w-3.5" />Complete</button><button type="button" onClick={() => void handleDelete(row.id)} className="rounded-lg bg-rose-50 px-2.5 py-1.5 text-xs font-semibold text-rose-700"><Trash2 className="mr-1 inline h-3.5 w-3.5" />Delete</button></div> },
              ]}
              data={data.items}
              loading={loading}
              emptyTitle="No reminders found"
              emptyDescription="Create a deadline reminder to get started."
              page={data.page}
              totalPages={data.total_pages}
              onPageChange={(nextPage) => void load(nextPage)}
            />
          </div>
        ) : loading ? <LoadingState message="Loading reminders..." /> : <EmptyState title="No reminders available" description="Create your first reminder using the form above." />}
      </section>
    </div>
  );
}
