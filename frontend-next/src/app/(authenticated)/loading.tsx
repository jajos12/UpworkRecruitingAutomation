import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
    return (
        <div className="min-h-screen bg-background font-sans flex">
            {/* Sidebar Skeleton */}
            <div className="w-60 border-r border-zinc-800 bg-zinc-950/50 fixed inset-y-0 left-0 p-4 space-y-6 hidden md:block">
                <div className="h-8 w-8 bg-zinc-800/50 rounded-lg" />
                <div className="space-y-2">
                    <Skeleton className="h-9 w-full bg-zinc-800/30" />
                    <Skeleton className="h-9 w-full bg-zinc-800/30" />
                    <Skeleton className="h-9 w-full bg-zinc-800/30" />
                    <Skeleton className="h-9 w-full bg-zinc-800/30" />
                </div>
            </div>

            <div className="flex-1 flex flex-col md:pl-60 transition-all duration-300">
                {/* Header Skeleton */}
                <header className="h-16 border-b border-zinc-800/30 bg-zinc-950/30 flex items-center justify-between px-6">
                    <Skeleton className="h-9 w-64 bg-zinc-800/30 rounded-lg" />
                    <div className="flex items-center gap-3">
                        <Skeleton className="h-8 w-24 bg-zinc-800/30 rounded-full" />
                        <Skeleton className="h-8 w-8 bg-zinc-800/30 rounded-full" />
                    </div>
                </header>

                {/* Main Content Skeleton */}
                <main className="flex-1 p-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <Skeleton className="h-32 rounded-xl bg-zinc-800/20" />
                        <Skeleton className="h-32 rounded-xl bg-zinc-800/20" />
                        <Skeleton className="h-32 rounded-xl bg-zinc-800/20" />
                        <Skeleton className="h-32 rounded-xl bg-zinc-800/20" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-96">
                        <Skeleton className="col-span-2 rounded-xl bg-zinc-800/20 h-full" />
                        <Skeleton className="col-span-1 rounded-xl bg-zinc-800/20 h-full" />
                    </div>
                </main>
            </div>
        </div>
    );
}
