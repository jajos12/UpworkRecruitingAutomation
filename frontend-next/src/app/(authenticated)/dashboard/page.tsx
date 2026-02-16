'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { JobWizard } from "@/features/jobs/components/JobWizard";
import { JobList } from "@/features/jobs/components/JobList";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SkeletonStats } from "@/components/ui/skeleton";
import { Plus, LayoutDashboard, Activity, Play, Briefcase, Users, Upload, Zap, ArrowUpRight, TrendingUp } from "lucide-react";
import { useWebSocket } from '@/hooks/useWebSocket';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runPipeline } from '@/features/settings/api';
import api from '@/lib/axios';
import { toast } from 'sonner';
import Link from 'next/link';

/* ─── Animated Counter ─── */
function AnimatedNumber({ value, className }: { value: number; className?: string }) {
  const [display, setDisplay] = useState(0);
  const prev = useRef(0);

  useEffect(() => {
    const start = prev.current;
    const diff = value - start;
    if (diff === 0) return;

    const duration = 500;
    const startTime = performance.now();
    let raf: number;

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    prev.current = value;
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return <span className={className}>{display}</span>;
}

/* ─── Tier Progress Bar ─── */
function TierBar({ t1, t2, t3, total }: { t1: number; t2: number; t3: number; total: number }) {
  if (total === 0) return <div className="h-1.5 rounded-full bg-zinc-800/50 w-full" />;
  const p1 = (t1 / total) * 100;
  const p2 = (t2 / total) * 100;
  const p3 = (t3 / total) * 100;

  return (
    <div className="h-1.5 rounded-full bg-zinc-800/50 w-full flex overflow-hidden">
      <motion.div initial={{ width: 0 }} animate={{ width: `${p1}%` }} transition={{ duration: 0.6, ease: 'easeOut' }} className="bg-emerald-500 rounded-l-full" />
      <motion.div initial={{ width: 0 }} animate={{ width: `${p2}%` }} transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }} className="bg-amber-500" />
      <motion.div initial={{ width: 0 }} animate={{ width: `${p3}%` }} transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }} className="bg-rose-500 rounded-r-full" />
    </div>
  );
}

export default function DashboardPage() {
  const [view, setView] = useState<'dashboard' | 'create'>('dashboard');
  const { lastMessage, status } = useWebSocket();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.get('/api/stats').then((r: { data: Record<string, number> }) => r.data),
  });

  const pipeline = useMutation({
    mutationFn: () => runPipeline({ fetch: true, analyze: true, communicate: true, dry_run: false }),
    onSuccess: () => toast.success('Pipeline started'),
    onError: (err: Error) => toast.error(`Pipeline failed: ${err.message}`),
  });

  if (view === 'create') {
    return (
      <div className="space-y-4 h-full">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => setView('dashboard')}
            className="text-zinc-400 hover:text-white pl-0 gap-2"
          >
            <LayoutDashboard className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>
        <JobWizard onSuccess={() => { setView('dashboard'); toast.success('Job created!'); }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Dashboard</h1>
          <p className="text-xs text-zinc-500 font-mono flex items-center gap-1.5 mt-0.5">
            SYS:
            <span className={status === 'connected' ? "text-emerald-400" : "text-amber-400"}>
              {status === 'connected' ? 'ONLINE' : 'CONNECTING'}
            </span>
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => pipeline.mutate()}
            loading={pipeline.isPending}
            variant="glow"
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run Pipeline
          </Button>
          <Button onClick={() => setView('create')}>
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            New Job
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {statsLoading ? (
        <SkeletonStats />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Jobs</span>
              <Briefcase className="h-3.5 w-3.5 text-zinc-600" />
            </div>
            <AnimatedNumber value={stats?.total_jobs ?? 0} className="text-2xl font-bold text-white tabular-nums" />
          </Card>

          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Candidates</span>
              <Users className="h-3.5 w-3.5 text-zinc-600" />
            </div>
            <AnimatedNumber value={stats?.total_proposals ?? 0} className="text-2xl font-bold text-white tabular-nums" />
          </Card>

          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Tier 1</span>
              <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
            </div>
            <AnimatedNumber value={stats?.tier1_count ?? 0} className="text-2xl font-bold text-emerald-400 tabular-nums" />
          </Card>

          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Pending</span>
              <Zap className="h-3.5 w-3.5 text-amber-500" />
            </div>
            <AnimatedNumber value={stats?.pending_count ?? 0} className="text-2xl font-bold text-amber-400 tabular-nums" />
          </Card>
        </div>
      )}

      {/* Tier Distribution Bar */}
      {stats && (
        <Card variant="glass" className="p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Tier Distribution</span>
            <div className="flex items-center gap-3 text-[10px] font-mono text-zinc-500">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Tier 1</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> Tier 2</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> Tier 3</span>
            </div>
          </div>
          <TierBar t1={stats.tier1_count} t2={stats.tier2_count} t3={stats.tier3_count} total={stats.total_proposals} />
        </Card>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-3 gap-3">
        <Link href="/jobs?action=create" className="group">
          <Card variant="glass" className="p-4 flex items-center gap-3 group-hover:border-zinc-700/50 transition-colors">
            <div className="h-8 w-8 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Briefcase className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-zinc-200">Create Job</p>
              <p className="text-[11px] text-zinc-500">Post a new position</p>
            </div>
            <ArrowUpRight className="h-3.5 w-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
          </Card>
        </Link>

        <Link href="/import" className="group">
          <Card variant="glass" className="p-4 flex items-center gap-3 group-hover:border-zinc-700/50 transition-colors">
            <div className="h-8 w-8 rounded-md bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
              <Upload className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-zinc-200">Bulk Import</p>
              <p className="text-[11px] text-zinc-500">Upload candidates</p>
            </div>
            <ArrowUpRight className="h-3.5 w-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
          </Card>
        </Link>

        <Link href="/candidates" className="group">
          <Card variant="glass" className="p-4 flex items-center gap-3 group-hover:border-zinc-700/50 transition-colors">
            <div className="h-8 w-8 rounded-md bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
              <Users className="h-4 w-4 text-violet-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-zinc-200">Candidates</p>
              <p className="text-[11px] text-zinc-500">Review all profiles</p>
            </div>
            <ArrowUpRight className="h-3.5 w-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
          </Card>
        </Link>
      </div>

      {/* Activity Feed */}
      <Card variant="glass" className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Live Activity</span>
          <div className={`h-1.5 w-1.5 rounded-full ${status === 'connected' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
        </div>
        <AnimatePresence mode="popLayout">
          {lastMessage ? (
            <motion.div
              key={lastMessage.timestamp}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-start gap-3"
            >
              <div className="h-6 w-6 rounded-md bg-zinc-800/50 flex items-center justify-center mt-0.5 shrink-0">
                <Activity className="h-3 w-3 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-mono tabular-nums">
                  {lastMessage.timestamp.split('T')[1]?.split('.')[0]}
                </p>
                <p className="text-sm text-zinc-300 mt-0.5 line-clamp-2">
                  {typeof lastMessage.payload === 'string' ? lastMessage.payload : JSON.stringify(lastMessage.payload)}
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 text-zinc-600 text-sm">
              <Activity className="w-3.5 h-3.5 animate-pulse" />
              Waiting for events...
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* Jobs List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Active Jobs</h2>
          <Link href="/jobs" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
            View all →
          </Link>
        </div>
        <JobList />
      </div>
    </div>
  );
}
