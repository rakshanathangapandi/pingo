import { useEffect, useState } from 'react';
import { CalendarClock, RefreshCw, Sparkles, Trophy } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { autoCollectReminders } from '@/api/reminders';
import { getCurrentChallenge } from '@/api/challenges';
import { listWheelEntries } from '@/api/wheel';
import { LoadingState } from '@/components/common/LoadingState';
import { SundayChallenge } from '@/types';
import { formatDate } from '@/utils/formatters';

export function AgentPage() {
  const [loading, setLoading] = useState(true);
  const [challenge, setChallenge] = useState<SundayChallenge | null>(null);
  const [wheelCount, setWheelCount] = useState(0);
  const [collecting, setCollecting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [ch, entries] = await Promise.all([getCurrentChallenge(), listWheelEntries(true)]);
      setChallenge(ch);
      setWheelCount(entries.length);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to load agent overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const handleAutoCollect = async () => {
    setCollecting(true);
    try {
      const result = await autoCollectReminders();
      toast.success(result.message);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to auto-collect reminders.');
    } finally {
      setCollecting(false);
    }
  };

  if (loading) return <LoadingState message="Loading agent overview..." />;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Automation</p>
        <h1 className="page-title">Agent</h1>
        <p className="mt-1 text-sm text-slate-500">One place for the wheel, Sunday challenge, and auto-collected reminders.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="card p-5">
          <div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-primary-600" /><h2 className="font-semibold">Random Wheel</h2></div>
          <p className="mt-2 text-sm text-slate-500">{wheelCount} active prize entries.</p>
          <Link to="/wheel" className="mt-3 inline-flex items-center rounded-lg bg-primary-50 px-3 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-100">Open wheel →</Link>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2"><Trophy className="h-5 w-5 text-primary-600" /><h2 className="font-semibold">Sunday Challenge</h2></div>
          <p className="mt-2 text-sm text-slate-500">{challenge ? challenge.title : 'No active challenge configured.'}</p>
          {challenge ? <p className="mt-1 text-xs text-slate-400">Date: {formatDate(challenge.challenge_date)}</p> : null}
          <Link to="/challenges" className="mt-3 inline-flex items-center rounded-lg bg-primary-50 px-3 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-100">Open challenges →</Link>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2"><CalendarClock className="h-5 w-5 text-primary-600" /><h2 className="font-semibold">Auto Reminders</h2></div>
          <p className="mt-2 text-sm text-slate-500">Reminders are auto-collected from wheel spins, challenges, gifts, and payments — no manual typing.</p>
          <button type="button" onClick={handleAutoCollect} disabled={collecting} className="mt-3 inline-flex items-center rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
            <RefreshCw className="mr-2 h-4 w-4" />{collecting ? 'Collecting…' : 'Collect now'}
          </button>
        </div>
      </section>

      <section className="card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Auto-collected reminders</h2>
          <Link to="/reminders" className="text-sm font-semibold text-primary-600">View all reminders →</Link>
        </div>
        <p className="text-sm text-slate-500">Reminders are generated automatically from your wheel spins, Sunday challenges, gift deliveries, and payment due dates. Visit the Reminders page to review, complete, or delete them.</p>
      </section>
    </div>
  );
}