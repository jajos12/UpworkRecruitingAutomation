'use client';

import { useJobs } from '../hooks/useJobs';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Users, Star, ArrowRight, Activity } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function JobList() {
  const { data: jobs, isLoading } = useJobs();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <div className="flex flex-col items-center gap-2 text-zinc-500 font-mono text-sm">
           <Loader2 className="animate-spin w-6 h-6" />
           LOADING_NODES...
        </div>
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center p-12 border border-dashed border-zinc-800 rounded-xl bg-zinc-950/50">
        <Activity className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
        <h3 className="text-zinc-300 font-medium">No Monitoring Nodes Active</h3>
        <p className="text-zinc-500 text-sm mt-2">Initialize a new job node to start tracking candidates.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {jobs.map(job => (
        <Card 
          key={job.job_id} 
          className="group flex flex-col h-full bg-zinc-950 border-zinc-800 hover:border-zinc-600 transition-all duration-300 cursor-pointer"
          onClick={() => router.push(`/jobs/${job.job_id}`)}
        >
          <CardHeader className="pb-3">
            <div className="flex justify-between items-start gap-4">
              <CardTitle className="text-base font-semibold leading-tight text-zinc-100 group-hover:text-white transition-colors">
                {job.title}
              </CardTitle>
              <div className="flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] flex-shrink-0 mt-1.5" title="Active" />
            </div>
            <div className="text-xs font-mono text-zinc-500 pt-1">ID: {job.job_id.substring(0, 8)}</div>
          </CardHeader>
          
          <CardContent className="flex-1 py-2">
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="bg-zinc-900/50 rounded p-2 border border-zinc-900">
                <div className="text-xs text-zinc-500 mb-1 flex items-center gap-1"><Users className="w-3 h-3"/> Total</div>
                <div className="text-lg font-mono font-medium text-zinc-300">{job.proposal_count}</div>
              </div>
              <div className="bg-zinc-900/50 rounded p-2 border border-zinc-900">
                <div className="text-xs text-emerald-500/80 mb-1 flex items-center gap-1"><Star className="w-3 h-3"/> Top Tier</div>
                <div className="text-lg font-mono font-medium text-emerald-400">{job.tier1_count}</div>
              </div>
            </div>
          </CardContent>

          <CardFooter className="pt-3 border-t border-zinc-900">
            <Button 
              className="w-full bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-white border border-zinc-800 h-9 text-xs uppercase tracking-wide font-medium group-hover:border-zinc-700 transition-all"
              onClick={(e) => {
                e.stopPropagation(); // Prevent double navigation
                router.push(`/jobs/${job.job_id}`);
              }}
            >
              Details <ArrowRight className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100 transition-opacity" />
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
