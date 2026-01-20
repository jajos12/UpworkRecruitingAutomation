'use client';

import { Proposal } from '../types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from 'lucide-react'; // Wait, Lucide doesn't have Badge.
import { CheckCircle2, XCircle, AlertTriangle, ExternalLink, ThumbsUp, ThumbsDown, Minus, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUpdateProposalStatus } from '../hooks/useJobs';

interface CandidateDetailProps {
  proposal: Proposal | null;
}

export function CandidateDetail({ proposal }: CandidateDetailProps) {
  const updateStatus = useUpdateProposalStatus();

  if (!proposal) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-4">
        <div className="w-16 h-16 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center">
          <UserIcon className="w-8 h-8 opacity-50" />
        </div>
        <p>Select a candidate to view AI analysis.</p>
      </div>
    );
  }

  const { freelancer, ai_score, ai_reasoning, ai_tier, status } = proposal;

  const handleStatusUpdate = (newStatus: string) => {
    updateStatus.mutate({ id: proposal.proposal_id, status: newStatus });
  };

  const isApproved = status === 'approved' || status.includes('tier1');
  const isRejected = status === 'rejected';

  return (
    <div className="h-full flex flex-col bg-zinc-950 overflow-y-auto">
      {/* Header Profile Section */}
      <div className="p-6 border-b border-zinc-800 bg-zinc-950 sticky top-0 z-10">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">{freelancer.name}</h2>
            <p className="text-zinc-400 font-mono text-sm mb-4">{freelancer.title}</p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {freelancer.skills.slice(0, 5).map(skill => (
                <span key={skill} className="px-2 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-xs font-mono">
                  {skill}
                </span>
              ))}
              {freelancer.skills.length > 5 && (
                <span className="px-2 py-1 text-zinc-500 text-xs font-mono">+{freelancer.skills.length - 5}</span>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
             <div className={cn(
               "flex flex-col items-center justify-center w-24 h-24 rounded-xl border-2 bg-zinc-900/50 backdrop-blur-sm",
               (ai_score || 0) >= 80 ? "border-emerald-500/50 text-emerald-500" :
               (ai_score || 0) >= 50 ? "border-yellow-500/50 text-yellow-500" :
               "border-red-500/50 text-red-500"
             )}>
                <span className="text-3xl font-bold tracking-tighter">{ai_score || '?'}</span>
                <span className="text-[10px] font-mono text-zinc-500 uppercase mt-1">AI Score</span>
             </div>
             
             <div className="flex gap-2">
               <Button 
                size="sm" 
                variant={isApproved ? "default" : "outline"} 
                className={cn(
                  "h-8 transition-colors",
                  isApproved ? "bg-emerald-600 hover:bg-emerald-700 text-white border-transparent" : "text-emerald-500 border-emerald-900 hover:bg-emerald-950"
                )}
                onClick={() => handleStatusUpdate('approved')}
                disabled={updateStatus.isPending}
               >
                 {updateStatus.isPending ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <ThumbsUp className="w-3 h-3 mr-2" />} 
                 {isApproved ? 'Approved' : 'Approve'}
               </Button>
               
               <Button 
                size="sm" 
                variant={isRejected ? "destructive" : "outline"} 
                className={cn(
                  "h-8 transition-colors",
                  isRejected ? "bg-red-600 hover:bg-red-700 text-white border-transparent" : "text-red-500 border-red-900 hover:bg-red-950"
                )}
                onClick={() => handleStatusUpdate('rejected')}
                disabled={updateStatus.isPending}
               >
                 <ThumbsDown className="w-3 h-3 mr-2" /> 
                 {isRejected ? 'Rejected' : 'Reject'}
               </Button>
             </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* AI Analysis Section */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
            <span className="w-1.5 h-4 bg-emerald-500 rounded-sm"></span>
            AI Analysis
          </h3>
          <Card className="bg-zinc-900/30 border-zinc-800">
            <CardContent className="p-4 space-y-4">
               {ai_reasoning ? (
                 <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">{ai_reasoning}</p>
               ) : (
                 <div className="flex items-center gap-2 text-zinc-500 text-sm italic">
                   <div className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse"></div>
                   Analysis text unavailable.
                 </div>
               )}
            </CardContent>
          </Card>
        </section>

        {/* Proposal / Cover Letter */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
            <span className="w-1.5 h-4 bg-blue-500 rounded-sm"></span>
            Cover Letter
          </h3>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 font-serif text-zinc-300 leading-7 whitespace-pre-wrap selection:bg-blue-500/30">
            {proposal.cover_letter}
          </div>
        </section>

        {/* Raw Data (JSON) - For "Technical" feel */}
        <section className="space-y-2 pt-8 border-t border-zinc-800/50">
           <details className="group">
             <summary className="flex items-center gap-2 text-xs font-mono text-zinc-600 cursor-pointer hover:text-zinc-400">
                <span className="group-open:rotate-90 transition-transform">▸</span>
                VIEW_RAW_METADATA_JSON
             </summary>
             <pre className="mt-4 bg-black border border-zinc-800 p-4 rounded-md text-[10px] text-zinc-500 font-mono overflow-auto max-h-40">
               {JSON.stringify(proposal, null, 2)}
             </pre>
           </details>
        </section>
      </div>
    </div>
  );
}

function UserIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}
