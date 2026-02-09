'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Wand2, FileText, Loader2, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Job } from '@/features/jobs/types';

interface RawInputFormProps {
  jobs: Job[];
  onParse: (jobId: string, rawText: string, formatHint?: string) => void;
  isParsing: boolean;
}

const FORMAT_OPTIONS = [
  { value: '', label: 'Auto-detect' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'csv', label: 'CSV' },
  { value: 'plain', label: 'Plain Text' },
  { value: 'json', label: 'JSON' },
];

const SAMPLE_DATA = `## Applicant 1: Sarah Chen
**Title:** Senior Full-Stack Developer
**Hourly Rate:** $75/hr
**Job Success:** 98%
**Total Earnings:** $125,000
**Status:** Top Rated Plus
**Skills:** React, Node.js, TypeScript, PostgreSQL, AWS, Docker
**Bio:** 8+ years building scalable web applications. Led engineering teams at two YC startups. Specializing in real-time systems and API design.
**Cover Letter:** I'm excited about this role because my experience with React and Node.js directly aligns with your requirements. At my previous role, I built a real-time dashboard that handled 10k concurrent users...
**Bid:** $3,500

---

## Applicant 2: Marcus Rivera
**Title:** Backend Python Developer
**Hourly Rate:** $45/hr
**Job Success:** 87%
**Total Earnings:** $32,000
**Skills:** Python, FastAPI, Django, PostgreSQL, Redis
**Bio:** 4 years of backend development experience. Strong focus on API development and database optimization.
**Cover Letter:** I have extensive experience with Python backend development and would love to contribute to your project. I've built similar systems using FastAPI...
**Bid:** $2,000

---

## Applicant 3: Priya Patel
**Title:** Full-Stack JavaScript Developer
**Hourly Rate:** $30/hr
**Job Success:** 72%
**Total Earnings:** $8,500
**Skills:** JavaScript, React, Express, MongoDB
**Cover Letter:** Hello, I am interested in your project. I can do this work quickly and efficiently.
**Bid:** $800`;

export function RawInputForm({ jobs, onParse, isParsing }: RawInputFormProps) {
  const [selectedJobId, setSelectedJobId] = useState('');
  const [rawText, setRawText] = useState('');
  const [formatHint, setFormatHint] = useState('');

  const handleParse = () => {
    if (!selectedJobId) {
      alert('Please select a job first');
      return;
    }
    if (rawText.length < 10) {
      alert('Please paste some applicant data first');
      return;
    }
    onParse(selectedJobId, rawText, formatHint || undefined);
  };

  const loadSample = () => {
    setRawText(SAMPLE_DATA);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Main Input Area */}
      <div className="lg:col-span-2 flex flex-col gap-4">
        <Card className="flex-1 flex flex-col border-zinc-800 bg-zinc-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="bg-zinc-800 text-zinc-400 w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono">1</span>
              Paste Raw Applicant Data
            </CardTitle>
            <CardDescription>
              Paste data in any format - markdown, CSV, plain text, JSON, or even messy notes. The AI will extract and organize everything.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-4">
            <div className="relative flex-1">
              <Textarea
                value={rawText}
                onChange={e => setRawText(e.target.value)}
                className="h-full min-h-[400px] bg-zinc-900 border-zinc-800 font-mono text-sm resize-none p-4 leading-relaxed"
                placeholder="Paste applicant profiles here...&#10;&#10;Supports any format:&#10;- Markdown with headers&#10;- CSV data&#10;- Plain text notes&#10;- JSON arrays&#10;- Copy-pasted from Upwork&#10;- Even messy, unstructured notes"
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-2">
                <span className="text-xs text-zinc-600 font-mono">
                  {rawText.length.toLocaleString()} chars
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={loadSample} className="text-zinc-500 hover:text-zinc-300">
                <FileText className="w-4 h-4 mr-2" />
                Load Sample Data
              </Button>
              <Button
                onClick={handleParse}
                disabled={isParsing || !selectedJobId || rawText.length < 10}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-6"
              >
                {isParsing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    AI Parsing...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4 mr-2" />
                    Parse with AI
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sidebar */}
      <div className="flex flex-col gap-4">
        {/* Job Selector */}
        <Card className="border-zinc-800 bg-zinc-950/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Select Job</CardTitle>
            <CardDescription className="text-xs">Which job are these applicants for?</CardDescription>
          </CardHeader>
          <CardContent>
            <select
              value={selectedJobId}
              onChange={e => setSelectedJobId(e.target.value)}
              className="w-full h-10 rounded-md border border-zinc-800 bg-zinc-900 px-3 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-zinc-600"
            >
              <option value="">Choose a job...</option>
              {jobs.map(job => (
                <option key={job.job_id} value={job.job_id}>
                  {job.title}
                </option>
              ))}
            </select>
            {jobs.length === 0 && (
              <p className="text-xs text-zinc-500 mt-2">
                No jobs found. Create a job first in the Jobs page.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Format Hint */}
        <Card className="border-zinc-800 bg-zinc-950/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Format Hint</CardTitle>
            <CardDescription className="text-xs">Help the AI understand the format (optional)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {FORMAT_OPTIONS.map(opt => (
                <label
                  key={opt.value}
                  className={cn(
                    'flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors text-sm',
                    formatHint === opt.value
                      ? 'bg-zinc-800 text-white'
                      : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-300'
                  )}
                >
                  <input
                    type="radio"
                    name="format"
                    value={opt.value}
                    checked={formatHint === opt.value}
                    onChange={e => setFormatHint(e.target.value)}
                    className="accent-emerald-500"
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Help */}
        <Card className="border-zinc-800 bg-zinc-950/50">
          <CardContent className="pt-4">
            <div className="flex items-start gap-2 text-xs text-zinc-500">
              <Info className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-zinc-400 mb-1">Tips</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>Separate applicants with --- or blank lines</li>
                  <li>Include names, skills, rates, and cover letters</li>
                  <li>The AI handles messy data - don't worry about formatting</li>
                  <li>Max 100,000 characters per paste</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
