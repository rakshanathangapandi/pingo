import { useState } from 'react';
import { LockKeyhole, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';

export function LoginPage() {
  const [email, setEmail] = useState('admin@pingo.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await loginUser(email, password);
      navigate('/', { replace: true });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to sign in.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl bg-white shadow-2xl lg:grid-cols-2">
        <section className="relative hidden bg-slate-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_42%)]" />
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-sky-500/10 px-3 py-1.5 text-sm font-medium text-sky-300"><ShieldCheck className="h-4 w-4" /> Pingo Admin</div>
            <h1 className="text-4xl font-bold tracking-tight">Manage your company operations from one place.</h1>
            <p className="mt-5 max-w-md text-slate-300">Track reminders, requests, payments, assets, gifts, challenges, and notifications through a single secure dashboard.</p>
          </div>
          <div className="relative grid gap-3 text-sm text-slate-300">
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Role-based access control</div>
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Automated reminders and notifications</div>
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Complete operational visibility</div>
          </div>
        </section>

        <section className="p-8 sm:p-12">
          <div className="mx-auto max-w-sm">
            <div className="mb-8">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">Welcome back</p>
              <h2 className="mt-2 text-3xl font-bold text-slate-900">Sign in</h2>
              <p className="mt-2 text-sm text-slate-500">Use your company account to access the admin dashboard.</p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="label" htmlFor="email">Email address</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input id="email" type="email" autoComplete="email" className="input pl-10" value={email} onChange={(event) => setEmail(event.target.value)} required />
                </div>
              </div>

              <div>
                <label className="label" htmlFor="password">Password</label>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input id="password" type="password" autoComplete="current-password" className="input pl-10" value={password} onChange={(event) => setPassword(event.target.value)} required />
                </div>
              </div>

              {error ? <div className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

              <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-600 px-4 py-3 font-semibold text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60">
                {isSubmitting ? 'Signing in...' : 'Sign in'}
              </button>
            </form>

            <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
              Demo access values are intentionally simple; use your created admin account in production.
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
