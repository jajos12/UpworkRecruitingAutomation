'use client';

import { useJobs } from '../hooks/useJobs';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SkeletonCard } from '@/components/ui/skeleton';
import { Users, Star, ArrowRight, Activity, Briefcase } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

export function JobList() {
  const { data: jobs, isLoading } = useJobs();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center py-16 border border-dashed border-zinc-800/50 rounded-lg glass-subtle">
        <div className="h-12 w-12 rounded-xl bg-zinc-800/30 border border-zinc-700/30 flex items-center justify-center mx-auto mb-4">
          <Briefcase className="w-5 h-5 text-zinc-600" />
        </div>
        <h3 className="text-zinc-300 font-medium text-sm">No Jobs Yet</h3>
        <p className="text-zinc-600 text-xs mt-1.5 max-w-xs mx-auto">Create your first job to start tracking and analyzing candidates.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {jobs.map((job, index) => (
        <motion.div
          key={job.job_id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05, duration: 0.3 }}
        >
          <Card
            variant="glass"
            className="group flex flex-col h-full cursor-pointer hover:border-zinc-600/50 transition-all duration-200"
            onClick={() => router.push(`/jobs/${job.job_id}`)}
          >
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start gap-3">
                <CardTitle className="text-sm font-semibold leading-snug text-zinc-200 group-hover:text-white transition-colors">
                  {job.title}
                </CardTitle>
                <div className="flex h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)] shrink-0 mt-1.5" title="Active" />
              </div>
              <span className="text-[10px] font-mono text-zinc-600 mt-1">{job.job_id.substring(0, 8)}</span>
            </CardHeader>

            <CardContent className="flex-1 py-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-md bg-zinc-900/30 border border-zinc-800/30 p-2.5">
                  <div className="text-[10px] text-zinc-500 mb-0.5 flex items-center gap-1"><Users className="w-3 h-3" /> Total</div>
                  <div className="text-lg font-mono font-semibold text-zinc-300 tabular-nums">{job.proposal_count}</div>
                </div>
                <div className="rounded-md bg-emerald-500/5 border border-emerald-500/10 p-2.5">
                  <div className="text-[10px] text-emerald-500/70 mb-0.5 flex items-center gap-1"><Star className="w-3 h-3" /> Tier 1</div>
                  <div className="text-lg font-mono font-semibold text-emerald-400 tabular-nums">{job.tier1_count}</div>
                </div>
              </div>
            </CardContent>

            <CardFooter className="pt-2 border-t border-zinc-800/30">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-zinc-500 hover:text-white text-[11px] uppercase tracking-wider h-8"
                onClick={(e) => {
                  e.stopPropagation();
                  router.push(`/jobs/${job.job_id}`);
                }}
              >
                View Details <ArrowRight className="w-3 h-3 ml-1.5 opacity-50 group-hover:opacity-100 transition-opacity" />
              </Button>
            </CardFooter>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
