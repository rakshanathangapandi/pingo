import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, CircleX, ClipboardList, Plus, Search, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { approveRequest, completeRequest, createRequest, deleteRequest, listRequests, rejectRequest } from '@/api/requests';
import { DataTable } from '@/components/common/DataTable';
import { LoadingState } from '@/components/common/LoadingState';
import { StatusBadge } from '@/components/common/StatusBadge';
import { PaginatedResponse, RequestItem, RequestStatus, RequestType } from '@/types';
import { formatDate, formatStatus, priorityTone, requestTone } from '@/utils/formatters';

const emptyForm = { title: '', description: '', request_type: 'other', priority: 'medium', due_date: '', assignee_id: '', supporting_documents: '' };

export function RequestsPage() {
  const [data, setData] = useState<PaginatedResponse<RequestItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState<RequestStatus | 'all'>('all');
  const [search, setSearch] = useState('');
  const [form, setForm] = useState(emptyForm);
  const [page, setPage] = useState(1);

  const load = async (nextPage = page) => {
    setLoading(true);
    try {
      setData(await listRequests({ page: nextPage, page_size: 10, status: status === 'all' ? undefined : status, search: search || undefined }));
    } catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Unable to load requests.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(1); }, [status, search]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    try { await createRequest({ ...form, assignee_id: form.assignee_id ? Number(form.assignee_id) : undefined, supporting_documents: form.supporting_documents ? form.supporting_documents.split(',').map((item) => item.trim()).filter(Boolean) : [] }); toast.success('Request created'); setForm(emptyForm); await load(1); }
    catch (caughtError) { toast.error(caughtError instanceof Error ? caughtError.message : 'Unable to create request.'); }
  };

  const action = async (fn: () => Promise<RequestItem | void>, label: string) => { try { await fn(); toast.success(label); await load(); } catch (caughtError) { toast.error(caughtError instanceof Error ? caughtError.message : `Unable to ${label.toLowerCase()}.`); } };

  const filters = useMemo(() => <div className="flex flex-wrap gap-3"><input className="input max-w-xs" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search requests" /><select className="input" value={status} onChange={(event) => setStatus(event.target.value as RequestStatus | 'all')}><option value="all">All statuses</option><option value="pending">Pending</option><option value="under_review">Under review</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="completed">Completed</option></select><button type="button" onClick={() => void load(1)} className="button-secondary"><Search className="mr-2 h-4 w-4" />Refresh</button></div>, [search, status, load]);

  return <div className="space-y-6"><header className="flex items-center justify-between"><div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Operations</p><h1 className="page-title">Request management</h1></div></header>
    <section className="card p-5"><div className="mb-5 flex items-center gap-2"><ClipboardList className="h-5 w-5 text-primary-600" /><h2 className="font-semibold text-slate-900">Create request</h2></div><form className="grid gap-4 md:grid-cols-2" onSubmit={submit}><div><label className="label">Title<input className="input" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label></div><div><label className="label">Request type<select className="input" value={form.request_type} onChange={(event) => setForm({ ...form, request_type: event.target.value as RequestType })}><option value="payment">Payment</option><option value="approval">Approval</option><option value="document">Document</option><option value="asset">Asset</option><option value="other">Other</option></select></label></div><div><label className="label">Due date<input type="date" className="input" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} /></label></div><div><label className="label">Priority<select className="input" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label></div><div className="md:col-span-2"><label className="label">Description<textarea className="input min-h-24" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label></div><div className="md:col-span-2"><label className="label">Assignee ID<input type="number" className="input" value={form.assignee_id} onChange={(event) => setForm({ ...form, assignee_id: event.target.value })} /></label></div><div className="md:col-span-2"><label className="label">Supporting documents (comma-separated URLs)<input className="input" value={form.supporting_documents} onChange={(event) => setForm({ ...form, supporting_documents: event.target.value })} /></label></div><button type="submit" className="button-primary md:col-span-2"><Plus className="mr-2 h-4 w-4" />Create request</button></form></section>
    <section className="card p-5">{filters}{error ? <div className="mt-4 text-sm text-rose-700">{error}</div> : null}{data && !loading ? <DataTable columns={[{ key: 'request', label: 'Request', render: (row) => <><div className="font-medium text-slate-800">{row.title}</div><div className="mt-1 text-xs text-slate-500">{row.request_id} • {row.request_type}</div></> }, { key: 'due', label: 'Due date', render: (row) => formatDate(row.due_date || row.requested_date) }, { key: 'priority', label: 'Priority', render: (row) => <StatusBadge tone={priorityTone(row.priority)}>{formatStatus(row.priority)}</StatusBadge> }, { key: 'status', label: 'Status', render: (row) => <StatusBadge tone={requestTone(row.status)}>{formatStatus(row.status)}</StatusBadge> }, { key: 'assignee', label: 'Assignee', render: (row) => row.assignee?.full_name || row.assignee?.email || 'Unassigned' }, { key: 'actions', label: 'Actions', render: (row) => <div className="flex flex-wrap gap-2"><button type="button" disabled={row.status === 'approved' || row.status === 'completed' || row.status === 'rejected'} onClick={() => void action(() => approveRequest(row.id), 'Approved')} className="rounded-lg bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white disabled:opacity-40"><CheckCircle2 className="mr-1 inline h-3.5 w-3.5" />Approve</button><button type="button" disabled={row.status === 'rejected' || row.status === 'completed'} onClick={() => void action(() => rejectRequest(row.id, 'Rejected from admin console'), 'Rejected')} className="rounded-lg bg-rose-100 px-2.5 py-1.5 text-xs font-semibold text-rose-700 disabled:opacity-40"><CircleX className="mr-1 inline h-3.5 w-3.5" />Reject</button><button type="button" disabled={row.status === 'completed'} onClick={() => void action(() => completeRequest(row.id), 'Completed')} className="rounded-lg bg-sky-100 px-2.5 py-1.5 text-xs font-semibold text-sky-700 disabled:opacity-40">Complete</button><button type="button" onClick={() => void action(() => deleteRequest(row.id), 'Deleted')} className="rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700"><Trash2 className="mr-1 inline h-3.5 w-3.5" />Delete</button></div> }]} data={data.items} loading={loading} emptyTitle="No requests found" emptyDescription="Create a request using the form above." page={data.page} totalPages={data.total_pages} onPageChange={(nextPage) => { void load(nextPage); setPage(nextPage); }} /> : <LoadingState message="Loading requests..." />}</section></div>;
}
