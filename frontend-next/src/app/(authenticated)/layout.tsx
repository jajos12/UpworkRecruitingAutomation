'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from "@/components/layout/AppShell";
import { Loader2 } from 'lucide-react';

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    // Basic client-side protection
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.push('/login');
    } else {
      setAuthorized(true);
    }
  }, [router]);

  if (!authorized) {
      return (
          <div className="h-screen w-full flex items-center justify-center bg-zinc-950">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
          </div>
      )
  }

  return (
    <AppShell>
      {children}
    </AppShell>
  );
}
