'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAllProposals } from '@/features/jobs/hooks/useJobs';
import { CandidateList } from '@/features/jobs/components/CandidateList';
import { CandidateDetail } from '@/features/jobs/components/CandidateDetail';
import { SkeletonTable } from '@/components/ui/skeleton';
import { Users } from 'lucide-react';
import { Proposal } from '@/features/jobs/types';

export default function CandidatesPage() {
  const { data: proposals, isLoading } = useAllProposals();
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  useEffect(() => {
    if (proposals && proposals.length > 0 && !selectedProposal) {
      const sorted = [...proposals].sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));
      setSelectedProposal(sorted[0]);
    }
  }, [proposals]);

  if (isLoading) {
    return (
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-white">Candidates</h1>
            <p className="text-xs text-zinc-500 mt-0.5">Loading candidate registry...</p>
          </div>
        </div>
        <SkeletonTable rows={8} />
      </div>
    );
  }

  const allProposals = proposals || [];

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 px-0.5">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white flex items-center gap-2.5">
            Candidates
            <span className="text-[11px] font-mono text-zinc-500 bg-zinc-800/40 border border-zinc-700/30 px-2 py-0.5 rounded-full tabular-nums">
              {allProposals.length}
            </span>
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">Review and manage all candidate profiles</p>
        </div>
      </div>

      {/* Split pane */}
      <div className="flex flex-1 overflow-hidden rounded-lg glass-card">
        {/* Left: List */}
        <div className="w-[340px] shrink-0 h-full overflow-hidden border-r border-zinc-800/30">
          <CandidateList
            proposals={allProposals}
            selectedId={selectedProposal?.proposal_id}
            onSelect={setSelectedProposal}
          />
        </div>
        {/* Right: Detail */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedProposal?.proposal_id || 'empty'}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.15 }}
            className="flex-1 h-full overflow-hidden"
          >
            <CandidateDetail proposal={selectedProposal} />
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
