'use client';

import { SettingsForm } from '@/features/settings/components/SettingsForm';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
       <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-white">Settings</h1>
      </div>
       <SettingsForm />
    </div>
  );
}

