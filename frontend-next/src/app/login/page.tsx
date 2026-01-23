'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';
import { Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/login', {
        email,
        password,
      });

      // Save token
      const { access_token, user } = response.data;
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', access_token);
        localStorage.setItem('user_email', user.email);
        localStorage.setItem('user_id', user.id);
      }

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-lg p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Upwork Agent</h1>
          <p className="text-zinc-400">Sign in to access your recruitment dashboard</p>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-800 text-red-200 p-3 rounded mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 bg-zinc-950 border border-zinc-800 rounded focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none text-white placeholder-zinc-500 transition-all"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 bg-zinc-950 border border-zinc-800 rounded focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none text-white placeholder-zinc-500 transition-all"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center text-xs text-zinc-600">
           Protected by Supabase Auth
        </div>
      </div>
    </div>
  );
}
