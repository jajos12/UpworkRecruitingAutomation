'use client';

import { ImportWizard } from '@/features/import/components/ImportWizard';
import { Upload } from 'lucide-react';

export default function ImportPage() {
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-cyan-500/10 border border-cyan-500/15 flex items-center justify-center">
          <Upload className="w-4 h-4 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Bulk Import</h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Paste or drop applicant data — AI will structure it into profiles
          </p>
        </div>
      </div>
      <ImportWizard />
    </div>
  );
}
