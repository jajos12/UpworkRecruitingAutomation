'use client';

import { Bell, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Header() {
  const triggerCommandPalette = () => {
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      bubbles: true,
    });
    document.dispatchEvent(event);
  };

  return (
    <header className="h-14 border-b border-zinc-800/40 glass-subtle flex items-center justify-between px-6 sticky top-0 z-20">
      {/* Search trigger */}
      <button
        onClick={triggerCommandPalette}
        className="flex items-center gap-2 rounded-md border border-zinc-800/40 bg-zinc-900/30 px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-400 hover:border-zinc-700/40 transition-colors max-w-sm w-full"
      >
        <span className="text-zinc-600">Search or jump to...</span>
        <kbd className="ml-auto rounded border border-zinc-700/40 bg-zinc-800/40 px-1.5 py-0.5 text-[10px] font-mono text-zinc-500">
          ⌘K
        </kbd>
      </button>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Live latency indicator */}
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-500 border-r border-zinc-800/30 pr-3">
          <Activity className="h-3 w-3 text-emerald-500" />
          <span className="text-zinc-400 tabular-nums">45ms</span>
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-500 hover:text-zinc-300">
          <Bell className="h-4 w-4" />
        </Button>

        {/* Avatar */}
        <div className="h-7 w-7 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-zinc-700/40 flex items-center justify-center text-[10px] font-semibold text-zinc-300">
          U
        </div>
      </div>
    </header>
  );
}
