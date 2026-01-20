'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useJob, useJobProposals } from '@/features/jobs/hooks/useJobs';
import { CandidateList } from '@/features/jobs/components/CandidateList';
import { CandidateDetail } from '@/features/jobs/components/CandidateDetail';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { Proposal } from '@/features/jobs/types';

export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.id as string;
  
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);
  const { data: proposals, isLoading: isLoadingProposals } = useJobProposals(jobId);
  
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  // Auto-select first proposal on load
  useEffect(() => {
    if (proposals && proposals.length > 0 && !selectedProposal) {
      setSelectedProposal(proposals[0]);
    }
  }, [proposals]);

  if (isLoadingJob || isLoadingProposals) {
    return (
      <div className="flex h-screen items-center justify-center text-zinc-500 font-mono text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mr-3" />
        LOADING_JOB_CONTEXT...
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-4">
        <AlertCircle className="w-12 h-12 text-red-500" />
        <h2 className="text-xl font-bold text-white">Job Not Found</h2>
        <Button onClick={() => router.push('/dashboard')}>Return to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] overflow-hidden">
      {/* Top Bar */}
      <div className="h-14 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/dashboard')} className="text-zinc-400 hover:text-white">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
             <h1 className="text-sm font-bold text-white tracking-tight">{job.title}</h1>
             <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
               <span className="text-emerald-500">ACTIVE</span>
               <span>|</span>
               <span>ID: {jobId.substring(0,8)}</span>
               <span>|</span>
               <span>{proposals?.length || 0} Candidates</span>
             </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
           <Button size="sm" variant="outline" className="h-8 text-xs font-mono">
             <RefreshCw className="w-3 h-3 mr-2" /> Sync
           </Button>
        </div>
      </div>

      {/* Main Split View */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: List (320px fixed) */}
        <div className="w-[350px] shrink-0 h-full border-r border-zinc-800 bg-zinc-950">
           <CandidateList 
             proposals={proposals || []} 
             selectedId={selectedProposal?.proposal_id}
             onSelect={setSelectedProposal}
           />
        </div>

        {/* Right: Detail (Flexible) */}
        <div className="flex-1 h-full bg-zinc-950 overflow-hidden relative">
           <CandidateDetail proposal={selectedProposal} />
        </div>
      </div>
    </div>
  );
}
