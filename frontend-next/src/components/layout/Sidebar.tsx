'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Briefcase, 
  Users, 
  Settings, 
  TerminalSquare, 
  Bot
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/jobs', label: 'Jobs', icon: Briefcase },
  { href: '/candidates', label: 'Candidates', icon: Users },
  { href: '/logs', label: 'System Logs', icon: TerminalSquare },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col h-screen fixed left-0 top-0 z-30">
      <div className="h-16 flex items-center px-6 border-b border-zinc-800">
        <Bot className="w-6 h-6 mr-3 text-white" />
        <span className="font-bold text-lg tracking-tight">RecruitAgent</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive 
                  ? "bg-zinc-900 text-white border border-zinc-800" 
                  : "text-zinc-400 hover:text-white hover:bg-zinc-900/50 border border-transparent"
              )}
            >
              <Icon className="w-4 h-4 mr-3" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-zinc-800">
        <div className="bg-zinc-900/50 rounded-md p-3 border border-zinc-800">
          <p className="text-xs font-mono text-zinc-500 mb-1">SYSTEM_STATUS</p>
          <div className="flex items-center text-xs text-emerald-500 font-mono">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse" />
            ONLINE
          </div>
        </div>
      </div>
    </aside>
  );
}
