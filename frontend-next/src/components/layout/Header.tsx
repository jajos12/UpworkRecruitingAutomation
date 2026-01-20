'use client';

import { Bell, Command, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function Header() {
  return (
    <header className="h-16 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-20">
      <div className="flex items-center min-w-[300px]">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
          <Input 
            placeholder="Search jobs, candidates, or commands..." 
            className="pl-9 h-9 bg-zinc-900 border-zinc-800 focus-visible:ring-zinc-700 font-mono text-xs"
          />
          <div className="absolute right-2.5 top-2.5 flex items-center gap-1 pointer-events-none">
            <kbd className="h-5 select-none items-center gap-1 rounded border border-zinc-800 bg-zinc-900 px-1.5 font-mono text-[10px] font-medium text-zinc-400 opacity-100 flex">
              <span className="text-xs">⌘</span>K
            </kbd>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 border-r border-zinc-800 pr-4">
          <span>API_LATENCY:</span>
          <span className="text-zinc-300">45ms</span>
        </div>
        
        <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white">
          <Bell className="h-4 w-4" />
        </Button>
        <div className="h-8 w-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-zinc-300">
          U
        </div>
      </div>
    </header>
  );
}
