export default function Loading() {
    return (
        <div className="flex h-screen w-full items-center justify-center bg-zinc-950">
            <div className="flex flex-col items-center gap-4">
                <div className="relative h-12 w-12">
                    <div className="absolute inset-0 rounded-full border-t-2 border-emerald-500 animate-spin"></div>
                    <div className="absolute inset-2 rounded-full border-t-2 border-emerald-400/50 animate-spin animation-delay-150"></div>
                </div>
                <p className="text-zinc-500 text-sm font-mono animate-pulse">INITIALIZING_AGENT...</p>
            </div>
        </div>
    );
}
