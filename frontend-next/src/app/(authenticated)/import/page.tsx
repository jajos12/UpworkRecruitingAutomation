'use client';

import { ImportWizard } from '@/features/import/components/ImportWizard';

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Bulk Import</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Paste raw applicant data and let AI organize it into structured profiles
        </p>
      </div>
      <ImportWizard />
    </div>
  );
}
