'use client';

import { useState } from 'react';
import { RawInputForm } from './RawInputForm';
import { ParsedReview } from './ParsedReview';
import { useParseRawText, useConfirmImport } from '../hooks/useImport';
import { useJobs, useAnalyzeJob } from '@/features/jobs/hooks/useJobs';
import { ParsedApplicant } from '../types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, ArrowRight, Users, Zap, ExternalLink } from 'lucide-react';
import Link from 'next/link';

type Step = 'input' | 'review' | 'success';

export function ImportWizard() {
  const [step, setStep] = useState<Step>('input');
  const [parsedApplicants, setParsedApplicants] = useState<ParsedApplicant[]>([]);
  const [parseWarnings, setParseWarnings] = useState<string[]>([]);
  const [importedJobId, setImportedJobId] = useState('');
  const [importResult, setImportResult] = useState<{ count: number; failed: number } | null>(null);

  const { data: jobs = [] } = useJobs();
  const parseMutation = useParseRawText();
  const confirmMutation = useConfirmImport();
  const analyzeJob = useAnalyzeJob();

  const handleParse = async (jobId: string, rawText: string, formatHint?: string) => {
    try {
      const result = await parseMutation.mutateAsync({ jobId, rawText, formatHint });
      setParsedApplicants(result.applicants);
      setParseWarnings(result.parse_warnings);
      setImportedJobId(jobId);

      if (result.applicants.length > 0) {
        setStep('review');
      } else {
        alert('No applicants could be extracted from the text. Try a different format or more detailed data.');
      }
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to parse the data. Please try again.');
    }
  };

  const handleConfirm = async (applicants: ParsedApplicant[], autoAnalyze: boolean) => {
    try {
      const result = await confirmMutation.mutateAsync({
        job_id: importedJobId,
        applicants,
        auto_analyze: autoAnalyze,
      });

      setImportResult({
        count: result.imported_count,
        failed: result.failed.length,
      });
      setStep('success');
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to import applicants. Please try again.');
    }
  };

  const handleReset = () => {
    setStep('input');
    setParsedApplicants([]);
    setParseWarnings([]);
    setImportResult(null);
  };

  // Step indicator
  const steps = [
    { key: 'input', label: 'Paste Data', num: 1 },
    { key: 'review', label: 'Review', num: 2 },
    { key: 'success', label: 'Done', num: 3 },
  ];

  const currentStepIndex = steps.findIndex(s => s.key === step);

  return (
    <div className="space-y-6">
      {/* Step Indicator */}
      <div className="flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s.key} className="flex items-center">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono border transition-colors ${
                i < currentStepIndex
                  ? 'bg-emerald-600 border-emerald-600 text-white'
                  : i === currentStepIndex
                    ? 'bg-zinc-800 border-emerald-500 text-emerald-400'
                    : 'bg-zinc-900 border-zinc-700 text-zinc-600'
              }`}>
                {i < currentStepIndex ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span className={`text-sm font-medium ${
                i <= currentStepIndex ? 'text-zinc-300' : 'text-zinc-600'
              }`}>
                {s.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`w-12 h-px mx-3 ${
                i < currentStepIndex ? 'bg-emerald-600' : 'bg-zinc-800'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      {step === 'input' && (
        <RawInputForm
          jobs={jobs}
          onParse={handleParse}
          isParsing={parseMutation.isPending}
        />
      )}

      {step === 'review' && (
        <ParsedReview
          applicants={parsedApplicants}
          warnings={parseWarnings}
          jobId={importedJobId}
          onConfirm={handleConfirm}
          onBack={() => setStep('input')}
          isConfirming={confirmMutation.isPending}
        />
      )}

      {step === 'success' && importResult && (
        <Card className="border-emerald-900/50 bg-emerald-950/10">
          <CardContent className="py-12 flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-950/50 border border-emerald-800/50 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Import Complete</h2>
            <p className="text-zinc-400 mb-1">
              Successfully imported <span className="text-emerald-400 font-semibold">{importResult.count}</span> applicant{importResult.count !== 1 ? 's' : ''}
            </p>
            {importResult.failed > 0 && (
              <p className="text-yellow-500 text-sm mb-4">
                {importResult.failed} failed to import
              </p>
            )}
            <p className="text-xs text-zinc-500 mb-6">
              Applicants are now in the pipeline and ready for AI analysis.
            </p>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={handleReset}>
                <Users className="w-4 h-4 mr-2" />
                Import More
              </Button>
              <Link href="/candidates">
                <Button className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  View Candidates
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
