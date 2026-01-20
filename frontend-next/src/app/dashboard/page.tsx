'use client';

import { useState } from 'react';
import { JobWizard } from "@/features/jobs/components/JobWizard";
import { JobList } from "@/features/jobs/components/JobList";
import { Button } from "@/components/ui/button";
import { Plus, LayoutDashboard, Activity } from "lucide-react";
import { useWebSocket } from '@/hooks/useWebSocket';

export default function DashboardPage() {
  const [view, setView] = useState<'dashboard' | 'create'>('dashboard');
  const { lastMessage, status } = useWebSocket();

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
        <JobWizard onSuccess={() => setView('dashboard')} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-white">Dashboard</h1>
          <p className="text-sm text-zinc-400 font-mono flex items-center gap-2">
            SYSTEM_STATUS: 
            <span className={status === 'connected' ? "text-emerald-500" : "text-yellow-500"}>
              {status === 'connected' ? 'ONLINE' : 'CONNECTING...'}
            </span>
          </p>
        </div>
        <Button 
          onClick={() => setView('create')} 
          className="bg-white text-black hover:bg-zinc-200"
        >
          <Plus className="w-4 h-4 mr-2" />
          Initialize New Job Node
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-zinc-950 border border-zinc-800">
          <div className="text-zinc-400 text-xs font-mono uppercase mb-2">Active Jobs</div>
          <div className="text-3xl font-bold text-white">3</div>
        </div>
        <div className="p-6 rounded-xl bg-zinc-950 border border-zinc-800">
          <div className="text-zinc-400 text-xs font-mono uppercase mb-2">Pending Reviews</div>
          <div className="text-3xl font-bold text-emerald-400">12</div>
        </div>
        <div className="p-6 rounded-xl bg-zinc-950 border border-zinc-800 relative overflow-hidden">
          <div className="text-zinc-400 text-xs font-mono uppercase mb-2">System Activity</div>
           {lastMessage ? (
             <div className="animate-in slide-in-from-bottom-2 fade-in duration-300">
               <div className="text-xs text-zinc-500 font-mono mb-1">
                  {lastMessage.timestamp.split('T')[1].split('.')[0]}
               </div>
               <div className="text-sm text-zinc-200 line-clamp-2">
                  {typeof lastMessage.payload === 'string' ? lastMessage.payload : JSON.stringify(lastMessage.payload)}
               </div>
             </div>
           ) : (
             <div className="flex items-center gap-2 text-zinc-600 text-sm mt-2">
               <Activity className="w-4 h-4 animate-pulse" />
               Monitoring events...
             </div>
           )}
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Active Monitoring Nodes</h2>
        </div>
        <JobList />
      </div>
    </div>
  );
}
