import { Inbox } from 'lucide-react';

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 text-center">
      <Inbox className="h-8 w-8 text-slate-400" />
      <h3 className="mt-3 text-sm font-semibold text-slate-800">{title}</h3>
      {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
    </div>
  );
}
