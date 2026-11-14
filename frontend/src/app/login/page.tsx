'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ShieldCheck, ArrowLeft } from 'lucide-react';
import Cookies from 'js-cookie';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import api, { getApiErrorMessage } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await api.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (res.data.access_token) {
        Cookies.set('token', res.data.access_token);
        router.push('/dashboard');
      } else {
        setError('The server did not return an access token. Please check the backend response.');
      }
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to login. Check that the backend is running, then verify your email and password.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-6 inline-flex items-center gap-2 text-sm text-slate-300 transition hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-3 rounded-2xl bg-cyan-500/15 p-3 text-cyan-300">
            <ShieldCheck className="h-9 w-9" />
          </div>
          <h1 className="text-3xl font-bold text-white">BuildGuard AI</h1>
          <p className="mt-2 text-sm text-slate-400">Welcome back! Sign in to continue your review workflow.</p>
        </div>

        <Card className="border-slate-200 bg-white shadow-2xl shadow-slate-950/40">
          <CardHeader>
            <CardTitle className="text-slate-900">Sign in</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="architect@buildguard.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                labelClassName="text-slate-800"
                className="border-slate-300 bg-white text-slate-900 placeholder:text-slate-500"
              />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                labelClassName="text-slate-800"
                className="border-slate-300 bg-white text-slate-900 placeholder:text-slate-500"
              />

              {error && (
                <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Need an account?{' '}
              <Link href="/register" className="font-medium text-cyan-300 hover:text-cyan-200">
                Create one
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
