'use client';

import { JobList } from "@/features/jobs/components/JobList";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { JobWizard } from "@/features/jobs/components/JobWizard";
import { useState } from "react";

export default function JobsPage() {
  const [isCreating, setIsCreating] = useState(false);

  if (isCreating) {
    return (
       <div className="space-y-4 h-full">
         <div className="flex items-center justify-between">
           <Button variant="ghost" onClick={() => setIsCreating(false)}>
             ← Back to Jobs
           </Button>
         </div>
         <JobWizard onSuccess={() => setIsCreating(false)} />
       </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-white">Jobs</h1>
        <Button onClick={() => setIsCreating(true)} className="bg-white text-black hover:bg-zinc-200">
          <Plus className="w-4 h-4 mr-2" />
          Create Job
        </Button>
      </div>
      <JobList />
    </div>
  );
}
