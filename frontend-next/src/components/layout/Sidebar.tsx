'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Settings,
  TerminalSquare,
  Bot,
  Upload,
  PanelLeftClose,
  PanelLeft,
  Search,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, shortcut: '1' },
  { href: '/jobs', label: 'Jobs', icon: Briefcase, shortcut: '2' },
  { href: '/candidates', label: 'Candidates', icon: Users, shortcut: '3' },
  { href: '/import', label: 'Bulk Import', icon: Upload, shortcut: '4' },
  { href: '/logs', label: 'System Logs', icon: TerminalSquare, shortcut: '5' },
  { href: '/settings', label: 'Settings', icon: Settings, shortcut: '6' },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'glass fixed left-0 top-0 z-30 flex h-screen flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center justify-between border-b border-zinc-800/50 px-4">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="relative shrink-0">
            <Bot className="h-5 w-5 text-emerald-400" />
            <div className="absolute -bottom-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="text-sm font-semibold tracking-tight whitespace-nowrap"
            >
              RecruitAgent
            </motion.span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-zinc-500 hover:text-zinc-300 transition-colors p-1 rounded-md hover:bg-zinc-800/50"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      {/* Search hint */}
      {!collapsed && (
        <div className="px-3 pt-4 pb-2">
          <button
            onClick={() => {
              const event = new KeyboardEvent('keydown', {
                key: 'k',
                ctrlKey: true,
                bubbles: true,
              });
              document.dispatchEvent(event);
            }}
            className="flex w-full items-center gap-2 rounded-md border border-zinc-800/50 bg-zinc-900/40 px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-400 hover:border-zinc-700/50 transition-colors"
          >
            <Search className="h-3 w-3" />
            <span>Search...</span>
            <kbd className="ml-auto rounded border border-zinc-700/50 bg-zinc-800/50 px-1.5 py-0.5 text-[10px] font-mono text-zinc-500">
              ⌘K
            </kbd>
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-2 px-2 space-y-0.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              prefetch={true}
              className={cn(
                'relative flex items-center rounded-md text-sm font-medium transition-all duration-150',
                collapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2',
                isActive
                  ? 'text-white bg-emerald-500/8'
                  : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/40'
              )}
              title={collapsed ? item.label : undefined}
            >
              {/* Active indicator bar */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="nav-active-indicator"
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                />
              )}

              <Icon className={cn('h-4 w-4 shrink-0', isActive && 'text-emerald-400')} />

              {!collapsed && (
                <>
                  <span className="ml-2.5">{item.label}</span>
                  <kbd className="ml-auto rounded border border-zinc-800/40 bg-zinc-900/40 px-1 py-0.5 text-[10px] font-mono text-zinc-600">
                    {item.shortcut}
                  </kbd>
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Status footer */}
      <div className="p-3 border-t border-zinc-800/40">
        <div className={cn(
          'rounded-md bg-zinc-900/30 border border-zinc-800/30',
          collapsed ? 'p-2 flex justify-center' : 'p-2.5'
        )}>
          {collapsed ? (
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          ) : (
            <>
              <p className="text-[10px] font-mono text-zinc-600 uppercase tracking-wider mb-1">System</p>
              <div className="flex items-center text-[11px] text-emerald-400 font-mono">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                Online
              </div>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
