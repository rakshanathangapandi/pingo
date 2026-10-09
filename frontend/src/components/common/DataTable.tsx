import { ChevronLeft, ChevronRight } from 'lucide-react';
import { ReactNode } from 'react';

export interface TableColumn<T> {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  loading: boolean;
  emptyTitle: string;
  emptyDescription?: string;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function DataTable<T>({ columns, data, loading, emptyTitle, page, totalPages, onPageChange }: DataTableProps<T>) {
  if (loading) return <div className="mt-5 text-sm text-slate-500">Loading records...</div>;
  if (!data.length) return <div className="mt-5 text-sm text-slate-500">{emptyTitle}</div>;

  return (
    <div className="mt-5 overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="text-slate-500">
          <tr>
            {columns.map((column) => <th key={column.key} className={`pb-3 pr-4 font-semibold ${column.className ?? ''}`}>{column.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="border-t border-slate-200">
              {columns.map((column) => <td key={`${index}-${column.key}`} className="py-3 pr-4 align-top">{column.render(row)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {totalPages > 1 ? (
        <div className="mt-5 flex items-center justify-end gap-2">
          <button type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} className="rounded-lg border border-slate-200 p-2 disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button>
          <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
          <button type="button" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} className="rounded-lg border border-slate-200 p-2 disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button>
        </div>
      ) : null}
    </div>
  );
}
