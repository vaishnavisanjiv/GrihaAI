'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ShieldCheck, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import api, { getApiErrorMessage } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/auth/register', {
        email,
        name,
        password,
      });

      router.push('/login');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to create account. Check that the backend is running and try again.'));
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
          <h1 className="text-3xl font-bold text-white">Create account</h1>
          <p className="mt-2 text-sm text-slate-400">Set up your BuildGuard workspace and start reviewing plans.</p>
        </div>

        <Card className="border-slate-200 bg-white shadow-2xl shadow-slate-950/40">
          <CardHeader>
            <CardTitle className="text-slate-900">Register</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4">
              <Input
                label="Full name"
                type="text"
                placeholder="Jane Architect"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                labelClassName="text-slate-800"
                className="border-slate-300 bg-white text-slate-900 placeholder:text-slate-500"
              />
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
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                labelClassName="text-slate-800"
                className="border-slate-300 bg-white text-slate-900 placeholder:text-slate-500"
              />

              {error && (
                <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-slate-400">
              Already have an account?{' '}
              <Link href="/login" className="font-medium text-cyan-300 hover:text-cyan-200">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
