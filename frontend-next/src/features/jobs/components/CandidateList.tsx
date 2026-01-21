'use client';

import { Proposal } from '../types';
import { cn } from '@/lib/utils';
import { DollarSign, Star, CheckCircle2, XCircle, LayoutGrid, List } from 'lucide-react';
import { useState, useMemo } from 'react';

interface CandidateListProps {
  proposals: Proposal[];
  selectedId?: string;
  onSelect: (proposal: Proposal) => void;
}

type ViewMode = 'list' | 'kanban';

export function CandidateList({ proposals, selectedId, onSelect }: CandidateListProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  // Group proposals for Kanban
  const groupedProposals = useMemo(() => {
    return {
      tier1: proposals.filter(p => !p.status?.includes('rejected') && (p.ai_tier === 1 || p.status === 'tier1' || p.status === 'approved')),
      tier2: proposals.filter(p => !p.status?.includes('rejected') && (p.ai_tier === 2 || p.status === 'tier2')),
      tier3: proposals.filter(p => p.status === 'rejected' || p.status === 'tier3' || p.ai_tier === 3),
      new: proposals.filter(p => !p.ai_tier && p.status !== 'rejected'),
    };
  }, [proposals]);

  // Sort by AI Score descending for ListView
  const sortedProposals = [...proposals].sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));

  return (
    <div className="flex flex-col h-full border-r border-zinc-800 bg-zinc-950/50">
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">Candidates</h3>
        <div className="flex items-center gap-2">
            <button 
                onClick={() => setViewMode('list')}
                className={cn("p-1 rounded hover:bg-zinc-800 transition-colors", viewMode === 'list' ? "text-emerald-400 bg-zinc-900" : "text-zinc-500")}
                title="List View"
            >
                <List className="w-4 h-4" />
            </button>
            <button 
                onClick={() => setViewMode('kanban')}
                className={cn("p-1 rounded hover:bg-zinc-800 transition-colors", viewMode === 'kanban' ? "text-emerald-400 bg-zinc-900" : "text-zinc-500")}
                title="Kanban Board"
            >
                <LayoutGrid className="w-4 h-4" />
            </button>
            <span className="text-xs bg-zinc-900 text-zinc-400 px-2 py-1 rounded-full border border-zinc-800 font-mono ml-2">
            {proposals.length}
            </span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto w-full scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        {proposals.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-sm">
            No candidates yet.
          </div>
        ) : viewMode === 'list' ? (
          <div className="divide-y divide-zinc-800/50">
            {sortedProposals.map((proposal) => {
              const isActive = selectedId === proposal.proposal_id;
              const isRejected = proposal.status === 'rejected';
              const isApproved = proposal.status === 'approved' || proposal.status?.includes('tier1');

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
        ) : (
          <div className="p-4 space-y-6">
            
            {/* New / Unclassified */}
             {groupedProposals.new.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 flex justify-between items-center bg-zinc-900/50 p-1.5 rounded">
                        <span>New / Unscored</span>
                        <span className="bg-zinc-800 text-zinc-300 px-1.5 rounded">{groupedProposals.new.length}</span>
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                        {groupedProposals.new.map(p => (
                            <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-zinc-500" />
                        ))}
                    </div>
                </div>
            )}

            {/* Tier 1 Column */}
            <div className="space-y-2">
                <h4 className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2 flex justify-between items-center bg-zinc-900/50 p-1.5 rounded border border-emerald-900/20">
                    <span>Top Match (Tier 1)</span>
                    <span className="bg-emerald-950 text-emerald-400 px-1.5 rounded border border-emerald-900/30">{groupedProposals.tier1.length}</span>
                </h4>
                <div className="grid grid-cols-1 gap-2">
                    {groupedProposals.tier1.map(p => (
                        <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-emerald-500" />
                    ))}
                    {groupedProposals.tier1.length === 0 && <div className="text-xs text-zinc-700 italic text-center py-2 border border-dashed border-zinc-800 rounded">No top candidates</div>}
                </div>
            </div>

            {/* Tier 2 Column */}
            <div className="space-y-2">
                <h4 className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2 flex justify-between items-center bg-zinc-900/50 p-1.5 rounded border border-blue-900/20">
                    <span>Potential (Tier 2)</span>
                    <span className="bg-blue-950 text-blue-400 px-1.5 rounded border border-blue-900/30">{groupedProposals.tier2.length}</span>
                </h4>
                 <div className="grid grid-cols-1 gap-2">
                    {groupedProposals.tier2.map(p => (
                        <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-blue-500" />
                    ))}
                </div>
            </div>

            {/* Rejected / Tier 3 Column */}
            <div className="space-y-2 pt-4 border-t border-zinc-800 mt-4">
                <div className="opacity-60 hover:opacity-100 transition-opacity">
                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2 flex justify-between items-center">
                        <span>Rejected / Low</span>
                        <span className="bg-zinc-800 text-zinc-500 px-1.5 rounded">{groupedProposals.tier3.length}</span>
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                        {groupedProposals.tier3.map(p => (
                            <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-zinc-700" isDimmed />
                        ))}
                    </div>
                </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

function KanbanCard({ proposal, onSelect, selectedId, color, isDimmed }: { proposal: Proposal, onSelect: any, selectedId?: string, color: string, isDimmed?: boolean }) {
    const isActive = selectedId === proposal.proposal_id;
    return (
        <button
            onClick={() => onSelect(proposal)}
            className={cn(
                "w-full text-left p-3 rounded bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800 transition-all shadow-sm group",
                isActive ? "ring-1 ring-emerald-500 bg-zinc-800" : "",
                `border-l-[3px] ${color}`,
                isDimmed && "opacity-60 hover:opacity-100 grayscale hover:grayscale-0"
            )}
        >
            <div className="flex justify-between items-start mb-1">
                <span className={cn("font-medium text-xs truncate w-[80%]", isActive ? "text-white" : "text-zinc-300 group-hover:text-zinc-100")}>
                    {proposal.freelancer.name}
                </span>
                {proposal.ai_score ? (
                    <span className={cn("text-[10px] font-mono font-bold", proposal.ai_score >= 80 ? "text-emerald-500" : proposal.ai_score >= 50 ? "text-yellow-500" : "text-zinc-500")}>
                        {proposal.ai_score}
                    </span>
                ) : null}
            </div>
            
            <div className="text-[10px] text-zinc-500 mb-2 line-clamp-1">{proposal.freelancer.title}</div>
            
            <div className="flex justify-between items-center">
                 <div className="flex gap-2">
                    <span className="text-[10px] bg-zinc-950 px-1.5 py-0.5 rounded text-zinc-400 font-mono border border-zinc-800">${proposal.bid_amount}</span>
                </div>
                {proposal.freelancer.job_success_score && (
                     <span className="text-[10px] text-zinc-600 flex items-center gap-0.5">
                        <Star className="w-2.5 h-2.5" />
                        {proposal.freelancer.job_success_score}%
                     </span>
                )}
            </div>
        </button>
    )
}
