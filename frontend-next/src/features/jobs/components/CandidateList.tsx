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

  const groupedProposals = useMemo(() => ({
    tier1: proposals.filter(p => !p.status?.includes('rejected') && (p.ai_tier === 1 || p.status === 'tier1' || p.status === 'approved')),
    tier2: proposals.filter(p => !p.status?.includes('rejected') && (p.ai_tier === 2 || p.status === 'tier2')),
    tier3: proposals.filter(p => p.status === 'rejected' || p.status === 'tier3' || p.ai_tier === 3),
    new: proposals.filter(p => !p.ai_tier && p.status !== 'rejected'),
  }), [proposals]);

  const sortedProposals = [...proposals].sort((a, b) => (b.ai_score || 0) - (a.ai_score || 0));

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-zinc-800/30 flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Candidates</span>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setViewMode('list')}
            className={cn("p-1 rounded transition-colors", viewMode === 'list' ? "text-emerald-400 bg-emerald-500/10" : "text-zinc-600 hover:text-zinc-400")}
          >
            <List className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setViewMode('kanban')}
            className={cn("p-1 rounded transition-colors", viewMode === 'kanban' ? "text-emerald-400 bg-emerald-500/10" : "text-zinc-600 hover:text-zinc-400")}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] text-zinc-500 font-mono bg-zinc-800/30 px-1.5 py-0.5 rounded ml-1 tabular-nums">
            {proposals.length}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto">
        {proposals.length === 0 ? (
          <div className="p-8 text-center text-zinc-600 text-xs">No candidates yet.</div>
        ) : viewMode === 'list' ? (
          <div className="divide-y divide-zinc-800/20">
            {sortedProposals.map((proposal) => {
              const isActive = selectedId === proposal.proposal_id;
              const isRejected = proposal.status === 'rejected';
              const isApproved = proposal.status === 'approved' || proposal.status?.includes('tier1');
              const score = proposal.ai_score || 0;
              let scoreColor = "text-zinc-600";
              if (score >= 80) scoreColor = "text-emerald-400";
              else if (score >= 50) scoreColor = "text-amber-400";

              return (
                <button
                  key={proposal.proposal_id}
                  onClick={() => onSelect(proposal)}
                  className={cn(
                    "w-full text-left px-3 py-2.5 transition-all relative",
                    isActive
                      ? "bg-emerald-500/5 border-l-2 border-emerald-500"
                      : "hover:bg-zinc-800/20 border-l-2 border-transparent",
                    isRejected && "opacity-35 grayscale hover:grayscale-0 hover:opacity-60"
                  )}
                >
                  <div className="flex justify-between items-start mb-0.5">
                    <span className={cn(
                      "font-medium text-xs truncate max-w-[180px] flex items-center gap-1.5",
                      isActive ? "text-white" : "text-zinc-300",
                      isApproved && "text-emerald-400"
                    )}>
                      {proposal.freelancer.name}
                      {isApproved && <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />}
                      {isRejected && <XCircle className="w-3 h-3 text-red-500 shrink-0" />}
                    </span>
                    <span className={cn("font-mono text-[10px] font-bold tabular-nums", scoreColor)}>
                      {score > 0 ? `${score}` : '-'}
                    </span>
                  </div>

                  <div className="text-[11px] text-zinc-500 truncate mb-1.5">{proposal.freelancer.title}</div>

                  <div className="flex items-center gap-2.5 text-[10px] text-zinc-600 font-mono">
                    <span className="flex items-center gap-0.5">
                      <DollarSign className="w-2.5 h-2.5" />
                      {proposal.bid_amount}
                    </span>
                    {proposal.freelancer.job_success_score && (
                      <span className="flex items-center gap-0.5">
                        <Star className="w-2.5 h-2.5 text-amber-500/50" />
                        {proposal.freelancer.job_success_score}%
                      </span>
                    )}
                  </div>

                  {proposal.ai_tier === 1 && !isRejected && !isApproved && (
                    <div className="absolute top-3 right-3 w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)]" />
                  )}
                </button>
              );
            })}
          </div>
        ) : (
          /* Kanban View */
          <div className="p-3 space-y-4">
            {groupedProposals.new.length > 0 && (
              <KanbanSection title="New / Unscored" count={groupedProposals.new.length} color="zinc">
                {groupedProposals.new.map(p => (
                  <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-zinc-500" />
                ))}
              </KanbanSection>
            )}

            <KanbanSection title="Top Match" count={groupedProposals.tier1.length} color="emerald">
              {groupedProposals.tier1.length === 0 ? (
                <div className="text-[10px] text-zinc-700 italic text-center py-2 border border-dashed border-zinc-800/30 rounded">No top candidates</div>
              ) : groupedProposals.tier1.map(p => (
                <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-emerald-500" />
              ))}
            </KanbanSection>

            <KanbanSection title="Potential" count={groupedProposals.tier2.length} color="blue">
              {groupedProposals.tier2.map(p => (
                <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-blue-500" />
              ))}
            </KanbanSection>

            <div className="pt-3 border-t border-zinc-800/20">
              <div className="opacity-50 hover:opacity-100 transition-opacity">
                <KanbanSection title="Rejected / Low" count={groupedProposals.tier3.length} color="zinc">
                  {groupedProposals.tier3.map(p => (
                    <KanbanCard key={p.proposal_id} proposal={p} onSelect={onSelect} selectedId={selectedId} color="border-l-zinc-700" isDimmed />
                  ))}
                </KanbanSection>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Sub-components ─── */

function KanbanSection({ title, count, color, children }: { title: string; count: number; color: string; children: React.ReactNode }) {
  const colorMap: Record<string, string> = {
    emerald: 'text-emerald-400 border-emerald-500/10 bg-emerald-500/5',
    blue: 'text-blue-400 border-blue-500/10 bg-blue-500/5',
    zinc: 'text-zinc-400 border-zinc-700/20 bg-zinc-800/20',
  };
  const badgeMap: Record<string, string> = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/15',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/15',
    zinc: 'bg-zinc-800/30 text-zinc-500 border-zinc-700/20',
  };

  return (
    <div className="space-y-1.5">
      <div className={cn("text-[10px] font-bold uppercase tracking-widest flex justify-between items-center p-1.5 rounded border", colorMap[color])}>
        <span>{title}</span>
        <span className={cn("px-1.5 rounded text-[10px] border", badgeMap[color])}>{count}</span>
      </div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function KanbanCard({ proposal, onSelect, selectedId, color, isDimmed }: {
  proposal: Proposal; onSelect: (p: Proposal) => void; selectedId?: string; color: string; isDimmed?: boolean;
}) {
  const isActive = selectedId === proposal.proposal_id;
  return (
    <button
      onClick={() => onSelect(proposal)}
      className={cn(
        "w-full text-left p-2.5 rounded-md bg-zinc-900/20 border border-zinc-800/20 hover:border-zinc-700/30 hover:bg-zinc-800/20 transition-all",
        isActive && "ring-1 ring-emerald-500/40 bg-emerald-500/5",
        `border-l-[3px] ${color}`,
        isDimmed && "opacity-50 hover:opacity-80 grayscale hover:grayscale-0"
      )}
    >
      <div className="flex justify-between items-start mb-0.5">
        <span className={cn("font-medium text-[11px] truncate w-[80%]", isActive ? "text-white" : "text-zinc-300")}>
          {proposal.freelancer.name}
        </span>
        {proposal.ai_score ? (
          <span className={cn("text-[10px] font-mono font-bold tabular-nums", proposal.ai_score >= 80 ? "text-emerald-400" : proposal.ai_score >= 50 ? "text-amber-400" : "text-zinc-500")}>
            {proposal.ai_score}
          </span>
        ) : null}
      </div>
      <div className="text-[10px] text-zinc-600 mb-1.5 line-clamp-1">{proposal.freelancer.title}</div>
      <div className="flex justify-between items-center">
        <span className="text-[10px] bg-zinc-800/20 px-1.5 py-0.5 rounded text-zinc-500 font-mono border border-zinc-800/20">${proposal.bid_amount}</span>
        {proposal.freelancer.job_success_score && (
          <span className="text-[10px] text-zinc-600 flex items-center gap-0.5">
            <Star className="w-2.5 h-2.5" />
            {proposal.freelancer.job_success_score}%
          </span>
        )}
      </div>
    </button>
  );
}
