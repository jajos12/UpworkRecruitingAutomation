'use client';

import { useState, useEffect } from 'react';
import { useAllProposals } from '@/features/jobs/hooks/useJobs';
import { CandidateList } from '@/features/jobs/components/CandidateList';
import { CandidateDetail } from '@/features/jobs/components/CandidateDetail';
import { RefreshCw } from 'lucide-react';
import { Proposal } from '@/features/jobs/types';

export default function CandidatesPage() {
  const { data: proposals, isLoading } = useAllProposals();
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  useEffect(() => {
    if (proposals && proposals.length > 0 && !selectedProposal) {
      // Sort by score to select the best one first, matching the list
      const sorted = [...proposals].sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));
      setSelectedProposal(sorted[0]);
    }
  }, [proposals]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500 font-mono text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mr-3" />
        LOADING_ALL_CANDIDATES...
      </div>
    );
  }

  const allProposals = proposals || [];

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] overflow-hidden">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-0 px-1 pt-1">
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
           Global Candidate Registry
           <span className="text-sm font-normal text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-full font-mono">
             {allProposals.length}
           </span>
        </h1>
      </div>

      <div className="flex flex-1 overflow-hidden border border-zinc-800 rounded-lg bg-zinc-950">
        <div className="w-[350px] flex-shrink-0 h-full overflow-hidden">
          <CandidateList 
            proposals={allProposals}
            selectedId={selectedProposal?.proposal_id}
            onSelect={setSelectedProposal}
          />
        </div>
        <div className="flex-1 h-full overflow-hidden">
           <CandidateDetail proposal={selectedProposal} />
        </div>
      </div>
    </div>
  );
}
