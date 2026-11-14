'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import {
  Home,
  Folder,
  Upload,
  Settings,
  ShieldCheck,
  LogOut,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/projects', label: 'Projects', icon: Folder },
  { href: '/upload', label: 'Upload Layout', icon: Upload },
  { href: '/settings', label: 'Settings', icon: Settings },
];

const publicRoutes = ['/', '/login', '/register'];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const showShell = !publicRoutes.includes(pathname ?? '/');
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    const token = Cookies.get('token');
    if (showShell && !token) {
      router.replace('/login');
    }
    queueMicrotask(() => {
      setAuthReady(true);
    });
  }, [pathname, router, showShell]);

  const handleSignOut = () => {
    Cookies.remove('token');
    router.push('/login');
  };

  if (!showShell) {
    return <>{children}</>;
  }

  if (!authReady) {
    return null;
  }

  const token = Cookies.get('token');
  if (!token) {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900">
      <aside className="flex w-72 flex-col bg-slate-950 text-white">
        <div className="flex items-center gap-3 border-b border-slate-800 p-5">
          <div className="rounded-xl bg-cyan-500/15 p-2 text-cyan-300">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">BuildGuard AI</h1>
            <p className="text-xs text-slate-400">Compliance workspace</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? 'bg-slate-800 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 p-4">
          <div className="mb-3 flex items-center gap-3 rounded-xl bg-slate-900/70 p-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 text-sm font-semibold text-white">
              U
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">User</p>
              <p className="text-xs text-slate-400">Architect</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleSignOut}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:border-slate-500 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-slate-50">{children}</main>
    </div>
  );
}
