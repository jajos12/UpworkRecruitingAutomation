'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';
import { Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.post('/api/auth/signup', {
        email,
        password,
      });

      if (response.data.access_token) {
        // Auto login
        const { access_token, user } = response.data;
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_token', access_token);
          localStorage.setItem('user_email', user.email);
          localStorage.setItem('user_id', user.id);
        }
        router.push('/dashboard');
      } else {
        // Email confirmation needed
        setSuccess(response.data.message || 'Signup successful! Please check your email.');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Signup failed. Please check your details.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-lg p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Create Account</h1>
          <p className="text-zinc-400">Join Upwork Recruitment Agent</p>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-800 text-red-200 p-3 rounded mb-6 text-sm">
            {error}
          </div>
        )}

        {success && (
           <div className="bg-emerald-900/50 border border-emerald-800 text-emerald-200 p-3 rounded mb-6 text-sm">
            {success}
            <div className="mt-2">
                <Link href="/login" className="underline font-bold">Go to Login</Link>
            </div>
          </div>
        )}

        {!success && (
          <form onSubmit={handleSignup} className="space-y-6">
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
                minLength={6}
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
                  Creating Account...
                </>
              ) : (
                'Sign Up'
              )}
            </button>
          </form>
        )}
        
        <div className="mt-6 text-center text-xs text-zinc-600">
           <Link href="/login" className="text-emerald-500 hover:underline">Already have an account? Sign In</Link>
        </div>
      </div>
    </div>
  );
}
