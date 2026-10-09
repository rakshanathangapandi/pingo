export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-primary-600" />
        {message}
      </div>
    </div>
  );
}
