'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { JobWizard } from "@/features/jobs/components/JobWizard";
import { JobList } from "@/features/jobs/components/JobList";
import { Button } from "@/components/ui/button";
import { Plus, ArrowLeft, Briefcase } from "lucide-react";
import { toast } from 'sonner';

export default function JobsPage() {
  const [isCreating, setIsCreating] = useState(false);

  if (isCreating) {
    return (
      <div className="space-y-4 h-full">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => setIsCreating(false)} className="text-zinc-400 hover:text-white gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Jobs
          </Button>
        </div>
        <JobWizard onSuccess={() => { setIsCreating(false); toast.success('Job created successfully'); }} />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Jobs</h1>
          <p className="text-xs text-zinc-500 mt-0.5">Manage job postings and track candidates</p>
        </div>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          Create Job
        </Button>
      </div>
      <JobList />
    </div>
  );
}
