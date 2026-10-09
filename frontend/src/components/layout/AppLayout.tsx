import { useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Bell, BriefcaseBusiness, CalendarClock, Gift, LogOut, Menu, PanelLeftClose, Sparkles, Trophy, Warehouse, WalletCards, X, Zap } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useApi } from '@/hooks/useApi';
import { request } from '@/api/client';
import { Notification } from '@/types';

const links = [
  { to: '/', label: 'Dashboard', icon: PanelLeftClose },
  { to: '/agent', label: 'Agent', icon: Zap },
  { to: '/reminders', label: 'Reminders', icon: CalendarClock },
  { to: '/requests', label: 'Requests', icon: BriefcaseBusiness },
  { to: '/payments', label: 'Payments', icon: WalletCards },
  { to: '/assets', label: 'Assets', icon: Warehouse },
  { to: '/challenges', label: 'Challenges', icon: Trophy },
  { to: '/wheel', label: 'Wheel', icon: Sparkles },
  { to: '/gifts', label: 'Gifts', icon: Gift },
  { to: '/notifications', label: 'Notifications', icon: Bell },
];

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const { data: notifications } = useApi(() => request<Notification[]>({ method: 'GET', url: '/notifications/recent?limit=5' }));
  const unreadCount = useMemo(() => notifications?.filter((item) => !item.is_read).length ?? 0, [notifications]);

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-slate-200 bg-slate-950 text-slate-100 transition-transform duration-200 ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-400">Pingo</p>
            <p className="text-sm font-semibold">Admin Console</p>
          </div>
          <button type="button" onClick={() => setMobileOpen(false)} className="rounded-lg p-2 text-slate-300 lg:hidden"><X className="h-5 w-5" /></button>
        </div>
        <nav className="space-y-1 p-4">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-sky-500 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}>
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute inset-x-4 bottom-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Signed in as</p>
          <p className="mt-1 font-semibold text-white">{user?.full_name || user?.email}</p>
          <p className="text-xs capitalize text-slate-400">{user?.role}</p>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6">
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-slate-600 lg:hidden"><Menu className="h-5 w-5" /></button>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-600">Management</p>
              <p className="text-sm font-semibold text-slate-800">{links.find((link) => location.pathname === link.to || (link.to !== '/' && location.pathname.startsWith(link.to)))?.label || 'Dashboard'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <NavLink to="/notifications" className="relative rounded-lg border border-slate-200 p-2.5 text-slate-600 transition hover:border-slate-300 hover:bg-slate-50" aria-label="Notifications">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 ? <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">{unreadCount}</span> : null}
            </NavLink>
            <button type="button" onClick={logout} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              <LogOut className="h-4 w-4" /> Logout
            </button>
          </div>
        </header>

        <main className="p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
