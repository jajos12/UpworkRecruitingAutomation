'use client';

import { SettingsForm } from '@/features/settings/components/SettingsForm';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-zinc-800/40 border border-zinc-700/30 flex items-center justify-center">
          <Settings className="w-4 h-4 text-zinc-400" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Settings</h1>
          <p className="text-xs text-zinc-500 mt-0.5">Configure AI providers, API keys, and system preferences</p>
        </div>
      </div>
      <SettingsForm />
    </div>
  );
}
