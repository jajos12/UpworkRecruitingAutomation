'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import {
    LayoutDashboard,
    Briefcase,
    Users,
    Upload,
    TerminalSquare,
    Settings,
    Search,
    Zap,
} from 'lucide-react';

const pages = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, group: 'Navigate' },
    { name: 'Jobs', href: '/jobs', icon: Briefcase, group: 'Navigate' },
    { name: 'Candidates', href: '/candidates', icon: Users, group: 'Navigate' },
    { name: 'Bulk Import', href: '/import', icon: Upload, group: 'Navigate' },
    { name: 'System Logs', href: '/logs', icon: TerminalSquare, group: 'Navigate' },
    { name: 'Settings', href: '/settings', icon: Settings, group: 'Navigate' },
];

const actions = [
    { name: 'Create New Job', href: '/jobs?action=create', icon: Briefcase, group: 'Actions' },
    { name: 'Import Candidates', href: '/import', icon: Upload, group: 'Actions' },
    { name: 'Run AI Analysis', href: '/jobs', icon: Zap, group: 'Actions' },
];

export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState('');
    const router = useRouter();

    // Toggle with cmd+k / ctrl+k
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((o) => !o);
            }
            if (e.key === 'Escape') {
                setOpen(false);
            }
        };
        document.addEventListener('keydown', down);
        return () => document.removeEventListener('keydown', down);
    }, []);

    const runCommand = useCallback(
        (href: string) => {
            setOpen(false);
            setSearch('');
            router.push(href);
        },
        [router]
    );

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={() => setOpen(false)}
            />

            {/* Palette */}
            <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-full max-w-lg">
                <Command shouldFilter={true}>
                    <div className="flex items-center px-4 border-b border-zinc-800/50">
                        <Search className="w-4 h-4 text-zinc-500 mr-2 shrink-0" />
                        <Command.Input
                            value={search}
                            onValueChange={setSearch}
                            placeholder="Search pages, actions..."
                        />
                    </div>
                    <Command.List>
                        <Command.Empty className="py-8 text-center text-sm text-zinc-500">
                            No results found.
                        </Command.Empty>

                        <Command.Group heading="Pages">
                            {pages.map((item) => (
                                <Command.Item
                                    key={item.href}
                                    value={item.name}
                                    onSelect={() => runCommand(item.href)}
                                >
                                    <item.icon className="w-4 h-4 text-zinc-400" />
                                    <span>{item.name}</span>
                                </Command.Item>
                            ))}
                        </Command.Group>

                        <Command.Separator />

                        <Command.Group heading="Quick Actions">
                            {actions.map((item) => (
                                <Command.Item
                                    key={item.name}
                                    value={item.name}
                                    onSelect={() => runCommand(item.href)}
                                >
                                    <item.icon className="w-4 h-4 text-emerald-400" />
                                    <span>{item.name}</span>
                                </Command.Item>
                            ))}
                        </Command.Group>
                    </Command.List>
                </Command>
            </div>
        </div>
    );
}
