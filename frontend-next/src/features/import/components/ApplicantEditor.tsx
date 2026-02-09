'use client';

import { useState } from 'react';
import { ParsedApplicant } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Check, X } from 'lucide-react';

interface ApplicantEditorProps {
  applicant: ParsedApplicant;
  onSave: (updated: ParsedApplicant) => void;
  onCancel: () => void;
}

export function ApplicantEditor({ applicant, onSave, onCancel }: ApplicantEditorProps) {
  const [name, setName] = useState(applicant.freelancer.name);
  const [title, setTitle] = useState(applicant.freelancer.title);
  const [hourlyRate, setHourlyRate] = useState(applicant.freelancer.hourly_rate?.toString() || '');
  const [jobSuccessScore, setJobSuccessScore] = useState(applicant.freelancer.job_success_score?.toString() || '');
  const [totalEarnings, setTotalEarnings] = useState(applicant.freelancer.total_earnings?.toString() || '');
  const [topRatedStatus, setTopRatedStatus] = useState(applicant.freelancer.top_rated_status || '');
  const [skills, setSkills] = useState(applicant.freelancer.skills?.join(', ') || '');
  const [bio, setBio] = useState(applicant.freelancer.bio || '');
  const [coverLetter, setCoverLetter] = useState(applicant.cover_letter);
  const [bidAmount, setBidAmount] = useState(applicant.bid_amount.toString());
  const [estimatedDuration, setEstimatedDuration] = useState(applicant.estimated_duration || '');
  const [profileUrl, setProfileUrl] = useState(applicant.freelancer.profile_url || '');

  const handleSave = () => {
    const updated: ParsedApplicant = {
      ...applicant,
      freelancer: {
        ...applicant.freelancer,
        name,
        title,
        hourly_rate: hourlyRate ? parseFloat(hourlyRate) : undefined,
        job_success_score: jobSuccessScore ? parseInt(jobSuccessScore) : undefined,
        total_earnings: totalEarnings ? parseFloat(totalEarnings) : undefined,
        top_rated_status: topRatedStatus || undefined,
        skills: skills.split(',').map(s => s.trim()).filter(Boolean),
        bio,
        profile_url: profileUrl || undefined,
      },
      cover_letter: coverLetter,
      bid_amount: parseFloat(bidAmount) || 0,
      estimated_duration: estimatedDuration || undefined,
    };
    onSave(updated);
  };

  return (
    <div className="space-y-4 p-4 border border-zinc-700 rounded-lg bg-zinc-900/80">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Name</Label>
          <Input value={name} onChange={e => setName(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Title</Label>
          <Input value={title} onChange={e => setTitle(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Hourly Rate ($)</Label>
          <Input type="number" value={hourlyRate} onChange={e => setHourlyRate(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Success Score</Label>
          <Input type="number" min="0" max="100" value={jobSuccessScore} onChange={e => setJobSuccessScore(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Total Earnings ($)</Label>
          <Input type="number" value={totalEarnings} onChange={e => setTotalEarnings(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Bid Amount ($)</Label>
          <Input type="number" value={bidAmount} onChange={e => setBidAmount(e.target.value)} className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Top Rated Status</Label>
          <Input value={topRatedStatus} onChange={e => setTopRatedStatus(e.target.value)} placeholder="e.g. Top Rated Plus" className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Duration</Label>
          <Input value={estimatedDuration} onChange={e => setEstimatedDuration(e.target.value)} placeholder="e.g. 2 weeks" className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-zinc-400 font-mono text-xs uppercase">Profile URL</Label>
          <Input value={profileUrl} onChange={e => setProfileUrl(e.target.value)} placeholder="https://..." className="bg-zinc-950 border-zinc-800 h-9" />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-zinc-400 font-mono text-xs uppercase">Skills (comma-separated)</Label>
        <Input value={skills} onChange={e => setSkills(e.target.value)} placeholder="Python, React, AWS..." className="bg-zinc-950 border-zinc-800 h-9" />
      </div>

      <div className="space-y-1.5">
        <Label className="text-zinc-400 font-mono text-xs uppercase">Bio</Label>
        <Textarea value={bio} onChange={e => setBio(e.target.value)} rows={3} className="bg-zinc-950 border-zinc-800 text-sm resize-none" />
      </div>

      <div className="space-y-1.5">
        <Label className="text-zinc-400 font-mono text-xs uppercase">Cover Letter</Label>
        <Textarea value={coverLetter} onChange={e => setCoverLetter(e.target.value)} rows={4} className="bg-zinc-950 border-zinc-800 text-sm resize-none" />
      </div>

      <div className="flex items-center justify-end gap-2 pt-2">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          <X className="w-4 h-4 mr-1" /> Cancel
        </Button>
        <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white" onClick={handleSave}>
          <Check className="w-4 h-4 mr-1" /> Save Changes
        </Button>
      </div>
    </div>
  );
}
