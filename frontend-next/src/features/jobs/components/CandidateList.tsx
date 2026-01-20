'use client';

import { Proposal } from '../types';
import { cn } from '@/lib/utils';
import { User, DollarSign, Star, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

interface CandidateListProps {
  proposals: Proposal[];
  selectedId?: string;
  onSelect: (proposal: Proposal) => void;
}

export function CandidateList({ proposals, selectedId, onSelect }: CandidateListProps) {
  // Sort by AI Score descending
  const sortedProposals = [...proposals].sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));

  return (
    <div className="flex flex-col h-full border-r border-zinc-800 bg-zinc-950/50">
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">Candidates</h3>
        <span className="text-xs bg-zinc-900 text-zinc-400 px-2 py-1 rounded-full border border-zinc-800 font-mono">
          {proposals.length}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {sortedProposals.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-sm">
            No candidates yet.
          </div>
        ) : (
          <div className="divide-y divide-zinc-800/50">
            {sortedProposals.map((proposal) => {
              const isActive = selectedId === proposal.proposal_id;
              const isRejected = proposal.status === 'rejected';
              const isApproved = proposal.status === 'approved' || proposal.status.includes('tier1');

              const score = proposal.ai_score || 0;
              let scoreColor = "text-zinc-500";
              if (score >= 80) scoreColor = "text-emerald-500";
              else if (score >= 50) scoreColor = "text-yellow-500";
              
              return (
                <button
                  key={proposal.proposal_id}
                  onClick={() => onSelect(proposal)}
                  className={cn(
                    "w-full text-left p-4 transition-all hover:bg-zinc-900/50 group relative",
                    isActive && "bg-zinc-900 border-l-2 border-emerald-500",
                    isRejected && "opacity-40 grayscale hover:grayscale-0 hover:opacity-75"
                  )}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={cn("font-medium text-sm truncate max-w-[150px] flex items-center gap-2", isActive ? "text-white" : "text-zinc-300", isApproved && "text-emerald-400")}>
                      {proposal.freelancer.name}
                      {isApproved && <CheckCircle2 className="w-3 h-3 text-emerald-500" />}
                      {isRejected && <XCircle className="w-3 h-3 text-red-500" />}
                    </span>
                    <span className={cn("font-mono text-xs font-bold", scoreColor)}>
                      {score > 0 ? `${score}/100` : '-'}
                    </span>
                  </div>
                  
                  <div className="text-xs text-zinc-500 truncate mb-2">
                    {proposal.freelancer.title}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs text-zinc-500 font-mono">
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      {proposal.bid_amount}
                    </span>
                    {proposal.freelancer.job_success_score && (
                      <span className="flex items-center gap-1 text-zinc-400">
                        <Star className="w-3 h-3 text-yellow-500/50" />
                        {proposal.freelancer.job_success_score}%
                      </span>
                    )}
                  </div>

                  {proposal.ai_tier === 1 && !isRejected && !isApproved && (
                     <div className="absolute top-4 right-12 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
