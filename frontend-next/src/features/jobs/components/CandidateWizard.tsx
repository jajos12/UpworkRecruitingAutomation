'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useCreateProposal } from '../hooks/useJobs';
import { ProposalCreate, FreelancerProfile } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { User, DollarSign, X, CheckCircle2 } from 'lucide-react';

export function CandidateWizard({ jobId, onSuccess, onCancel }: { jobId: string; onSuccess?: () => void; onCancel?: () => void }) {
  const { register, handleSubmit, formState: { errors, isSubmitting, isSubmitSuccessful } } = useForm<{
    name: string;
    title: string;
    skills: string;
    hourly_rate: number;
    cover_letter: string;
    bid_amount: number;
  }>();

  const createProposal = useCreateProposal();

  const onSubmit = (data: { name: string; title: string; skills: string; hourly_rate: number; cover_letter: string; bid_amount: number }) => {
    // Generate a pseudo-random ID for the freelancer if this is a manual entry
    const freelancerId = `manual-${Date.now()}`;
    
    // Parse skills from comma-separated string
    const skillList = data.skills.split(',').map(s => s.trim()).filter(s => s.length > 0);

    const freelancer: FreelancerProfile = {
      freelancer_id: freelancerId,
      name: data.name,
      title: data.title,
      skills: skillList,
      hourly_rate: data.hourly_rate,
      job_success_score: 0, // Default for manual
      total_earnings: 0, // Default for manual
    };

    const payload: ProposalCreate = {
      job_id: jobId,
      freelancer: freelancer,
      cover_letter: data.cover_letter,
      bid_amount: data.bid_amount,
    };

    createProposal.mutate(payload, {
      onSuccess: () => {
        if (onSuccess) onSuccess();
      }
    });
  };

  if (isSubmitSuccessful) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4 text-center">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
          <CheckCircle2 className="w-6 h-6 text-green-600" />
        </div>
        <h3 className="text-xl font-semibold">Candidate Added!</h3>
        <p className="text-muted-foreground">The candidate has been added to the job and will be analyzed shortly.</p>
        <Button onClick={onSuccess} className="mt-4">Done</Button>
      </div>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto border-0 shadow-none">
      <CardHeader>
        <CardTitle>Add Candidate</CardTitle>
        <CardDescription>Manually add a candidate proposal for this job.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium flex items-center gap-2">
              <User className="w-4 h-4" /> Freelancer Info
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input 
                  id="name" 
                  placeholder="e.g. John Doe" 
                  {...register('name', { required: 'Name is required' })} 
                />
                {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="title">Professional Title</Label>
                <Input 
                  id="title" 
                  placeholder="e.g. Senior Python Developer" 
                  {...register('title', { required: 'Title is required' })} 
                />
                {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="skills">Skills (comma separated)</Label>
              <Input 
                id="skills" 
                placeholder="Python, React, Django, AWS" 
                {...register('skills')} 
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="hourly_rate">Hourly Rate ($)</Label>
                    <Input 
                        id="hourly_rate" 
                        type="number" 
                        min="0"
                        step="0.01"
                        placeholder="50.00" 
                        {...register('hourly_rate', { valueAsNumber: true })} 
                    />
                </div>
            </div>
          </div>

          <div className="border-t pt-6 space-y-4">
            <h3 className="text-lg font-medium flex items-center gap-2">
              <DollarSign className="w-4 h-4" /> Proposal Details
            </h3>

            <div className="space-y-2">
                <Label htmlFor="bid_amount">Bid Amount / Rate ($)</Label>
                <Input 
                    id="bid_amount" 
                    type="number"
                    min="0" 
                    step="0.01"
                    placeholder="500.00" 
                    {...register('bid_amount', { required: 'Bid amount is required', valueAsNumber: true })} 
                />
                {errors.bid_amount && <p className="text-sm text-red-500">{errors.bid_amount.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="cover_letter">Cover Letter / Proposal Text</Label>
              <Textarea 
                id="cover_letter" 
                className="h-40"
                placeholder="Paste the cover letter here..." 
                {...register('cover_letter', { required: 'Cover letter is required', minLength: { value: 20, message: 'Too short' } })} 
              />
              {errors.cover_letter && <p className="text-sm text-red-500">{errors.cover_letter.message}</p>}
            </div>
          </div>

        </CardContent>
        <CardFooter className="flex justify-between border-t pt-6">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createProposal.isPending}>
            {isSubmitting || createProposal.isPending ? 'Adding...' : 'Add Candidate'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
