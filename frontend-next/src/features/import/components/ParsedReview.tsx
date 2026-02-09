'use client';

import { useState } from 'react';
import { ParsedApplicant } from '../types';
import { ApplicantEditor } from './ApplicantEditor';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import {
  AlertTriangle, ArrowLeft, CheckCircle2, Edit2, Loader2,
  Trash2, Upload, Users, Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ParsedReviewProps {
  applicants: ParsedApplicant[];
  warnings: string[];
  jobId: string;
  onConfirm: (applicants: ParsedApplicant[], autoAnalyze: boolean) => void;
  onBack: () => void;
  isConfirming: boolean;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const color = confidence >= 0.7 ? 'emerald' : confidence >= 0.4 ? 'yellow' : 'red';
  const label = confidence >= 0.7 ? 'High' : confidence >= 0.4 ? 'Medium' : 'Low';

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono',
      color === 'emerald' && 'bg-emerald-950/50 text-emerald-400 border border-emerald-800/50',
      color === 'yellow' && 'bg-yellow-950/50 text-yellow-400 border border-yellow-800/50',
      color === 'red' && 'bg-red-950/50 text-red-400 border border-red-800/50',
    )}>
      <div className={cn(
        'w-1.5 h-1.5 rounded-full',
        color === 'emerald' && 'bg-emerald-400',
        color === 'yellow' && 'bg-yellow-400',
        color === 'red' && 'bg-red-400',
      )} />
      {label} ({Math.round(confidence * 100)}%)
    </span>
  );
}

export function ParsedReview({ applicants: initial, warnings, jobId, onConfirm, onBack, isConfirming }: ParsedReviewProps) {
  const [applicants, setApplicants] = useState<ParsedApplicant[]>(initial);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [autoAnalyze, setAutoAnalyze] = useState(true);

  const removeApplicant = (index: number) => {
    setApplicants(prev => prev.filter((_, i) => i !== index));
    if (editingIndex === index) setEditingIndex(null);
  };

  const updateApplicant = (index: number, updated: ParsedApplicant) => {
    setApplicants(prev => prev.map((a, i) => i === index ? updated : a));
    setEditingIndex(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-1" /> Back
          </Button>
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Users className="w-5 h-5 text-emerald-500" />
              {applicants.length} Applicant{applicants.length !== 1 ? 's' : ''} Found
            </h2>
            <p className="text-xs text-zinc-500">Review and edit before importing</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoAnalyze}
              onChange={e => setAutoAnalyze(e.target.checked)}
              className="accent-emerald-500"
            />
            <Zap className="w-3.5 h-3.5" />
            Auto-analyze after import
          </label>
          <Button
            onClick={() => onConfirm(applicants, autoAnalyze)}
            disabled={isConfirming || applicants.length === 0}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-6"
          >
            {isConfirming ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Import {applicants.length} Applicant{applicants.length !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <Card className="border-yellow-900/50 bg-yellow-950/20">
          <CardContent className="pt-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 shrink-0" />
              <div className="space-y-1">
                {warnings.map((w, i) => (
                  <p key={i} className="text-sm text-yellow-400/80">{w}</p>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Applicant Cards */}
      <div className="space-y-4">
        {applicants.map((applicant, index) => (
          <div key={applicant.freelancer.freelancer_id + index}>
            {editingIndex === index ? (
              <ApplicantEditor
                applicant={applicant}
                onSave={updated => updateApplicant(index, updated)}
                onCancel={() => setEditingIndex(null)}
              />
            ) : (
              <Card className="border-zinc-800 bg-zinc-950/50 hover:border-zinc-700 transition-colors">
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between gap-4">
                    {/* Left: Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-white truncate">{applicant.freelancer.name}</h3>
                        <ConfidenceBadge confidence={applicant.confidence} />
                      </div>
                      <p className="text-sm text-zinc-400 mb-2">{applicant.freelancer.title}</p>

                      {/* Stats Row */}
                      <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-500 mb-3">
                        {applicant.freelancer.hourly_rate && (
                          <span>${applicant.freelancer.hourly_rate}/hr</span>
                        )}
                        {applicant.freelancer.job_success_score && (
                          <span className="text-emerald-500">{applicant.freelancer.job_success_score}% success</span>
                        )}
                        {applicant.freelancer.total_earnings && (
                          <span>${applicant.freelancer.total_earnings.toLocaleString()} earned</span>
                        )}
                        {applicant.bid_amount > 0 && (
                          <span className="font-medium text-white">Bid: ${applicant.bid_amount.toLocaleString()}</span>
                        )}
                        {applicant.freelancer.top_rated_status && (
                          <span className="text-yellow-500">{applicant.freelancer.top_rated_status}</span>
                        )}
                      </div>

                      {/* Skills */}
                      {applicant.freelancer.skills && applicant.freelancer.skills.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-3">
                          {applicant.freelancer.skills.slice(0, 8).map((skill, i) => (
                            <span key={i} className="px-2 py-0.5 bg-zinc-900 border border-zinc-800 rounded text-xs text-zinc-400">
                              {skill}
                            </span>
                          ))}
                          {applicant.freelancer.skills.length > 8 && (
                            <span className="px-2 py-0.5 text-xs text-zinc-600">
                              +{applicant.freelancer.skills.length - 8} more
                            </span>
                          )}
                        </div>
                      )}

                      {/* Cover Letter Preview */}
                      {applicant.cover_letter && (
                        <p className="text-xs text-zinc-500 line-clamp-2 italic">
                          &ldquo;{applicant.cover_letter.substring(0, 200)}{applicant.cover_letter.length > 200 ? '...' : ''}&rdquo;
                        </p>
                      )}

                      {/* Parse Notes */}
                      {applicant.parse_notes.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {applicant.parse_notes.map((note, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded bg-yellow-950/30 text-yellow-500/80 border border-yellow-900/30">
                              {note}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-1 shrink-0">
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-500 hover:text-white" onClick={() => setEditingIndex(index)}>
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-500 hover:text-red-400" onClick={() => removeApplicant(index)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ))}
      </div>

      {applicants.length === 0 && (
        <Card className="border-dashed border-zinc-800 bg-zinc-950/30">
          <CardContent className="py-12 flex flex-col items-center text-center">
            <Users className="w-8 h-8 text-zinc-700 mb-3" />
            <p className="text-zinc-500 text-sm">All applicants removed</p>
            <Button variant="ghost" size="sm" className="mt-2" onClick={onBack}>
              Go back and try again
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
