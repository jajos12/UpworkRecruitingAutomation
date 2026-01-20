'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useCreateJob, useGenerateCriteria } from '../hooks/useJobs';
import { JobCreate } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Wand2, Plus, X, AlertOctagon, CheckCircle2, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export function JobWizard({ onSuccess }: { onSuccess?: () => void }) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<{ title: string; description: string }>();
  
  // Local state for interactive criteria
  const [mustHaves, setMustHaves] = useState<string[]>([]);
  const [niceToHaves, setNiceToHaves] = useState<{ id: string; text: string; weight: number }[]>([]);
  const [redFlags, setRedFlags] = useState<string[]>([]);
  
  // Input states for adding new items manually
  const [newMustHave, setNewMustHave] = useState('');
  const [newRedFlag, setNewRedFlag] = useState('');

  const createJob = useCreateJob();
  const generateCriteria = useGenerateCriteria();
  const [isGenerating, setIsGenerating] = useState(false);

  const onSubmit = (data: { title: string; description: string }) => {
    const formattedData: JobCreate = {
      title: data.title,
      description: data.description,
      criteria: {
        must_have: mustHaves,
        nice_to_have: niceToHaves.map(({ text, weight }) => ({ text, weight })),
        red_flags: redFlags,
      }
    };

    createJob.mutate(formattedData, {
      onSuccess: () => {
        if (onSuccess) onSuccess();
      }
    });
  };

  const handleGenerate = async () => {
    const description = watch('description');
    if (!description || description.length < 20) {
      alert('Please enter a longer description first');
      return;
    }

    setIsGenerating(true);
    try {
      const criteria = await generateCriteria.mutateAsync(description);
      
      setMustHaves(criteria.must_have);
      setNiceToHaves(criteria.nice_to_have.map((item, idx) => ({ 
        ...item, 
        id: `gen-${idx}`,
        weight: Number(item.weight) || 1
      })));
      setRedFlags(criteria.red_flags);
    } catch (error) {
      console.error('Failed to generate', error);
      alert('Failed to generate criteria');
    } finally {
      setIsGenerating(false);
    }
  };

  // Helper to add items
  const addMustHave = () => {
    if (newMustHave.trim()) {
      setMustHaves([...mustHaves, newMustHave.trim()]);
      setNewMustHave('');
    }
  };

  const addRedFlag = () => {
    if (newRedFlag.trim()) {
      setRedFlags([...redFlags, newRedFlag.trim()]);
      setNewRedFlag('');
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-8rem)]">
      {/* LEFT COLUMN: Job Definition */}
      <Card className="flex flex-col h-full border-zinc-800 bg-zinc-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="bg-zinc-800 text-zinc-400 w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono">1</span>
            Job Definition
          </CardTitle>
          <CardDescription>Define the role and let AI extract the signals.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 flex-1 overflow-y-auto">
          <div className="space-y-2">
            <Label htmlFor="title" className="text-zinc-400 font-mono text-xs uppercase">Job Title</Label>
            <Input 
              id="title" 
              {...register('title', { required: true })} 
              placeholder="e.g. Senior Backend Engineer" 
              className="bg-zinc-900 border-zinc-800 focus:border-zinc-600 font-medium text-lg h-12"
            />
          </div>

          <div className="space-y-2 flex-1 flex flex-col min-h-[300px]">
            <Label htmlFor="description" className="text-zinc-400 font-mono text-xs uppercase">Job Description</Label>
            <div className="relative flex-1">
              <Textarea 
                id="description" 
                {...register('description', { required: true })} 
                className="h-full min-h-[300px] bg-zinc-900 border-zinc-800 font-mono text-sm resize-none p-4 leading-relaxed" 
                placeholder="Paste the full JD here..."
              />
              <div className="absolute bottom-4 right-4">
                <Button 
                  type="button" 
                  variant="default" // White button in dark mode
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="shadow-lg hover:shadow-xl transition-all"
                >
                  <Wand2 className={cn("w-4 h-4 mr-2", isGenerating && "animate-spin")} />
                  {isGenerating ? 'Scanning...' : 'Scan & Extract Criteria'}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* RIGHT COLUMN: Criteria Configuration */}
      <Card className="flex flex-col h-full border-zinc-800 bg-zinc-950/50">
        <CardHeader className="border-b border-zinc-800/50 pb-4">
          <CardTitle className="flex items-center gap-2">
            <span className="bg-zinc-800 text-zinc-400 w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono">2</span>
            Scoring Criteria
          </CardTitle>
          <CardDescription>Configure how candidates are ranked.</CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-0">
          <div className="divide-y divide-zinc-800/50">
            
            {/* Must Haves */}
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-emerald-500 font-mono text-xs uppercase flex items-center gap-2">
                  <CheckCircle2 className="w-3 h-3" /> Must Haves
                </Label>
                <span className="text-xs text-zinc-500">{mustHaves.length} items</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {mustHaves.map((item, idx) => (
                  <div key={idx} className="group flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-md px-3 py-1.5 text-sm text-zinc-300">
                    {item}
                    <button 
                       onClick={() => setMustHaves(mustHaves.filter((_, i) => i !== idx))}
                       className="text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                <div className="flex items-center gap-2 min-w-[200px]">
                  <Input 
                    value={newMustHave}
                    onChange={(e) => setNewMustHave(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addMustHave())}
                    placeholder="Add requirement..." 
                    className="h-8 text-xs bg-transparent border-dashed border-zinc-700 focus:border-emerald-500/50"
                  />
                  <Button size="icon" variant="ghost" className="h-8 w-8" onClick={addMustHave}>
                    <Plus className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Nice to Haves (Weighted) */}
            <div className="p-6 space-y-4 bg-zinc-900/20">
              <div className="flex items-center justify-between">
                <Label className="text-blue-400 font-mono text-xs uppercase flex items-center gap-2">
                  <TrendingUp className="w-3 h-3" /> Nice To Haves (Weighted)
                </Label>
              </div>
              <div className="space-y-3">
                {niceToHaves.map((item, idx) => (
                  <div key={item.id} className="flex items-center gap-4 bg-zinc-900/50 border border-zinc-800 p-3 rounded-lg group">
                    <span className="flex-1 text-sm text-zinc-300 font-medium">{item.text}</span>
                    
                    <div className="flex items-center gap-3 w-32">
                      <input 
                        type="range" 
                        min="1" 
                        max="20" 
                        value={item.weight}
                        onChange={(e) => {
                          const val = parseInt(e.target.value);
                          const newItems = [...niceToHaves];
                          newItems[idx].weight = val;
                          setNiceToHaves(newItems);
                        }}
                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:rounded-full"
                      />
                      <span className="font-mono text-xs text-blue-400 w-6 text-right">{item.weight}</span>
                    </div>

                     <button 
                       onClick={() => setNiceToHaves(niceToHaves.filter((_, i) => i !== idx))}
                       className="text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Red Flags */}
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-red-500 font-mono text-xs uppercase flex items-center gap-2">
                  <AlertOctagon className="w-3 h-3" /> Red Flags
                </Label>
              </div>
              <div className="flex flex-col gap-2">
                 {redFlags.map((item, idx) => (
                  <div key={idx} className="group flex items-center justify-between bg-red-950/10 border border-red-900/20 rounded-md px-3 py-2 text-sm text-red-300/80">
                    <span className="flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                       {item}
                    </span>
                    <button 
                       onClick={() => setRedFlags(redFlags.filter((_, i) => i !== idx))}
                       className="text-red-900 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                <div className="flex items-center gap-2">
                   <Input 
                    value={newRedFlag}
                    onChange={(e) => setNewRedFlag(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRedFlag())}
                    placeholder="Add red flag..." 
                    className="h-8 text-xs bg-transparent border-dashed border-zinc-700 focus:border-red-500/50"
                  />
                  <Button size="icon" variant="ghost" className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-950/30" onClick={addRedFlag}>
                    <Plus className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </div>

          </div>
        </CardContent>
        
        <CardFooter className="border-t border-zinc-800 p-4 bg-zinc-900/30">
          <Button 
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium h-10"
            onClick={handleSubmit(onSubmit)}
            disabled={createJob.isPending}
          >
            {createJob.isPending ? 'Initializing Job Node...' : 'Initialize Job & Start Monitoring'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
