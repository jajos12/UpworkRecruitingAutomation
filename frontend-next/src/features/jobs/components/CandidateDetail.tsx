'use client';

import { Proposal, InterviewGuide, InterviewQuestion, ChatMessage } from '../types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, XCircle, AlertTriangle, ExternalLink, ThumbsUp, ThumbsDown, Minus, Loader2, Sparkles, User as UserIcon, MessageSquare, ClipboardList, Mic, MicOff, Send, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUpdateProposalStatus, useAnalyzeProposal, useGenerateInterviewGuide, useChatWithCandidate } from '../hooks/useJobs';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from 'react';
import { Settings2 } from "lucide-react";
import ReactMarkdown from 'react-markdown';

interface CandidateDetailProps {
  proposal: Proposal | null;
}

export function CandidateDetail({ proposal }: CandidateDetailProps) {
  const updateStatus = useUpdateProposalStatus();
  const analyzeProposal = useAnalyzeProposal();
  const generateGuide = useGenerateInterviewGuide();
  const chatWithCandidate = useChatWithCandidate();

  const [interviewGuide, setInterviewGuide] = useState<InterviewGuide | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      (window as any).recognition?.stop();
    } else {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert("Browser does not support speech recognition.");
        return;
      }
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsRecording(true);
      recognition.onend = () => setIsRecording(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setMessageInput(prev => (prev ? prev + " " + transcript : transcript));
      };

      try {
        recognition.start();
        (window as any).recognition = recognition;
      } catch (e) {
        console.error("Speech recognition error:", e);
        setIsRecording(false);
      }
    }
  };

  const [configOpen, setConfigOpen] = useState(false);
  const [config, setConfig] = useState({
    behavioral_count: 1,
    technical_count: 2,
    red_flag_count: 1,
    soft_skill_count: 1,
    custom_focus: ""
  });

  useEffect(() => {
    if (proposal?.interview_questions) {
      setInterviewGuide({ proposal_id: proposal.proposal_id, questions: proposal.interview_questions });
    } else {
      setInterviewGuide(null);
    }

    if (proposal?.chat_history) {
      setChatHistory(proposal.chat_history);
    } else {
      setChatHistory([]);
    }
  }, [proposal]);

  const handleSendMessage = () => {
    if (!messageInput.trim() || !proposal) return;

    // Optimistic update
    const userMsg: ChatMessage = { role: 'user', content: messageInput, timestamp: new Date().toISOString() };
    setChatHistory(prev => [...prev, userMsg]);
    const currentInput = messageInput;
    setMessageInput("");

    chatWithCandidate.mutate({ proposalId: proposal.proposal_id, message: currentInput }, {
      onSuccess: (data) => {
        setChatHistory(prev => [...prev, data]);
      },
      onError: () => {
        // Rollback or show error
      }
    });
  };

  if (!proposal) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-4">
        <div className="w-16 h-16 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center">
          <UserIcon className="w-8 h-8 opacity-50" />
        </div>
        <p>Select a candidate to view AI analysis.</p>
      </div>
    );
  }

  const { freelancer, ai_score, ai_reasoning, ai_tier, status } = proposal;

  const handleStatusUpdate = (newStatus: string) => {
    updateStatus.mutate({ id: proposal.proposal_id, status: newStatus });
  };

  const handleGenerateInterview = () => {
    generateGuide.mutate({ proposalId: proposal.proposal_id, config }, {
      onSuccess: (data) => {
        setInterviewGuide(data);
        setConfigOpen(false);
      }
    });
  };

  const isApproved = status === 'approved' || status.includes('tier1');
  const isRejected = status === 'rejected';

  return (
    <div className="h-full flex flex-col overflow-y-auto">
      {/* Header Profile Section */}
      <div className="p-5 border-b border-zinc-800/30 glass-subtle sticky top-0 z-10">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-lg font-semibold text-white mb-0.5">{freelancer.name}</h2>
            <p className="text-zinc-500 font-mono text-xs mb-3">{freelancer.title}</p>

            <div className="flex flex-wrap gap-2 mb-4">
              {freelancer.skills.slice(0, 5).map(skill => (
                <span key={skill} className="px-1.5 py-0.5 rounded bg-zinc-800/30 border border-zinc-700/20 text-zinc-400 text-[11px] font-mono">
                  {skill}
                </span>
              ))}
              {freelancer.skills.length > 5 && (
                <span className="px-2 py-1 text-zinc-500 text-xs font-mono">+{freelancer.skills.length - 5}</span>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <div className={cn(
              "flex flex-col items-center justify-center w-24 h-24 rounded-xl border-2 bg-zinc-900/50 backdrop-blur-sm",
              (ai_score || 0) >= 80 ? "border-emerald-500/50 text-emerald-500" :
                (ai_score || 0) >= 50 ? "border-yellow-500/50 text-yellow-500" :
                  "border-red-500/50 text-red-500"
            )}>
              <span className="text-3xl font-bold tracking-tighter">{ai_score || '?'}</span>
              <span className="text-[10px] font-mono text-zinc-500 uppercase mt-1">AI Score</span>
            </div>

            <div className="flex gap-2">
              {!ai_score && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 text-indigo-400 border-indigo-900 hover:bg-indigo-950"
                  onClick={() => analyzeProposal.mutate(proposal.proposal_id)}
                  disabled={analyzeProposal.isPending}
                >
                  {analyzeProposal.isPending ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <Sparkles className="w-3 h-3 mr-2" />}
                  Analyze
                </Button>
              )}

              <Button
                size="sm"
                variant={isApproved ? "default" : "outline"}
                className={cn(
                  "h-8 transition-colors",
                  isApproved ? "bg-emerald-600 hover:bg-emerald-700 text-white border-transparent" : "text-emerald-500 border-emerald-900 hover:bg-emerald-950"
                )}
                onClick={() => handleStatusUpdate('approved')}
                disabled={updateStatus.isPending}
              >
                {updateStatus.isPending ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <ThumbsUp className="w-3 h-3 mr-2" />}
                {isApproved ? 'Approved' : 'Approve'}
              </Button>

              <Button
                size="sm"
                variant={isRejected ? "destructive" : "outline"}
                className={cn(
                  "h-8 transition-colors",
                  isRejected ? "bg-red-600 hover:bg-red-700 text-white border-transparent" : "text-red-500 border-red-900 hover:bg-red-950"
                )}
                onClick={() => handleStatusUpdate('rejected')}
                disabled={updateStatus.isPending}
              >
                <ThumbsDown className="w-3 h-3 mr-2" />
                {isRejected ? 'Rejected' : 'Reject'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="flex-1 flex flex-col">
        <div className="px-5 border-b border-zinc-800/30">
          <TabsList className="bg-transparent h-12 p-0 space-x-6">
            <TabsTrigger value="overview" className="h-full rounded-none border-b-2 border-transparent data-[state=active]:border-emerald-500 data-[state=active]:text-emerald-400 bg-transparent px-0 pb-0 text-zinc-400">Overview</TabsTrigger>
            <TabsTrigger value="interview" className="h-full rounded-none border-b-2 border-transparent data-[state=active]:border-emerald-500 data-[state=active]:text-emerald-400 bg-transparent px-0 pb-0 text-zinc-400 flex items-center gap-2">
              <ClipboardList className="w-3 h-3" /> Interview Guide
            </TabsTrigger>
            <TabsTrigger value="chat" className="h-full rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:text-blue-400 bg-transparent px-0 pb-0 text-zinc-400 flex items-center gap-2">
              <Bot className="w-3 h-3" /> Investigator
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">

          <TabsContent value="overview" className="m-0 p-5 space-y-6">
            {/* AI Analysis Section */}
            <section className="space-y-4">
              <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-4 bg-emerald-500 rounded-sm"></span>
                AI Analysis
              </h3>
              <Card variant="glass">
                <CardContent className="p-4 space-y-4">
                  {ai_reasoning ? (
                    <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">{ai_reasoning}</p>
                  ) : (
                    <div className="flex items-center gap-2 text-zinc-500 text-sm italic">
                      <div className="w-2 h-2 rounded-full bg-zinc-600 animate-pulse"></div>
                      Analysis text unavailable.
                    </div>
                  )}
                </CardContent>
              </Card>
            </section>

            {/* Proposal / Cover Letter */}
            <section className="space-y-4">
              <h3 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-4 bg-blue-500 rounded-sm"></span>
                Cover Letter
              </h3>
              <div className="glass-card rounded-lg p-5 font-serif text-zinc-300 leading-7 whitespace-pre-wrap selection:bg-blue-500/30">
                {proposal.cover_letter}
              </div>
            </section>

            {/* Raw Data (JSON) - For "Technical" feel */}
            <section className="space-y-2 pt-8 border-t border-zinc-800/50">
              <details className="group">
                <summary className="flex items-center gap-2 text-xs font-mono text-zinc-600 cursor-pointer hover:text-zinc-400">
                  <span className="group-open:rotate-90 transition-transform">▸</span>
                  VIEW_RAW_METADATA_JSON
                </summary>
                <pre className="mt-4 bg-black border border-zinc-800 p-4 rounded-md text-[10px] text-zinc-500 font-mono overflow-auto max-h-40">
                  {JSON.stringify(proposal, null, 2)}
                </pre>
              </details>
            </section>
          </TabsContent>

          <TabsContent value="interview" className="m-0 p-6 space-y-6">
            {!interviewGuide ? (
              <div className="flex flex-col items-center justify-center p-12 border border-dashed border-zinc-800 rounded-lg bg-zinc-900/20">
                <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                  <ClipboardList className="w-6 h-6 text-zinc-500" />
                </div>
                <h3 className="text-lg font-medium text-white mb-2">No Interview Guide Yet</h3>
                <p className="text-zinc-400 text-center max-w-sm mb-6 text-sm">
                  Generate a personalized interview script based on this candidate's specific profile gaps and strengths.
                </p>
                <div className="flex gap-2">
                  <Dialog open={configOpen} onOpenChange={setConfigOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="icon" className="border-dashed border-zinc-700 hover:bg-zinc-800 hover:border-zinc-600">
                        <Settings2 className="w-4 h-4 text-zinc-400" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-zinc-950 border-zinc-800 text-zinc-100 sm:max-w-md">
                      <DialogHeader>
                        <DialogTitle>Configure Interview Guide</DialogTitle>
                        <DialogDescription className="text-zinc-400">Customize how the AI generates interview questions.</DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label className="text-right text-zinc-500">Behavioral</Label>
                          <Input type="number" min={0} max={5} value={config.behavioral_count}
                            onChange={e => setConfig({ ...config, behavioral_count: parseInt(e.target.value) })}
                            className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label className="text-right text-zinc-500">Technical</Label>
                          <Input type="number" min={0} max={10} value={config.technical_count}
                            onChange={e => setConfig({ ...config, technical_count: parseInt(e.target.value) })}
                            className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label className="text-right text-zinc-500">Red Flags</Label>
                          <Input type="number" min={0} max={5} value={config.red_flag_count}
                            onChange={e => setConfig({ ...config, red_flag_count: parseInt(e.target.value) })}
                            className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label className="text-right text-zinc-500">Soft Skills</Label>
                          <Input type="number" min={0} max={5} value={config.soft_skill_count}
                            onChange={e => setConfig({ ...config, soft_skill_count: parseInt(e.target.value) })}
                            className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8" />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label className="text-right text-zinc-500">Focus</Label>
                          <Input placeholder="e.g. Async Python" value={config.custom_focus}
                            onChange={e => setConfig({ ...config, custom_focus: e.target.value })}
                            className="col-span-3 bg-zinc-900 border-zinc-800 text-white h-8" />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button onClick={handleGenerateInterview} disabled={generateGuide.isPending} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
                          {generateGuide.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                          Generate Custom Guide
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <Button onClick={handleGenerateInterview} disabled={generateGuide.isPending}>
                    {generateGuide.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                    Generate Guide with AI
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {interviewGuide.questions.map((q, idx) => (
                  <Card key={idx} className="bg-zinc-900 border-zinc-800 overflow-hidden">
                    <div className={cn("h-1 w-full",
                      q.type === 'Behavioral' ? "bg-blue-500" :
                        q.type === 'Technical' ? "bg-emerald-500" :
                          q.type === 'Red Flag' ? "bg-red-500" : "bg-purple-500"
                    )} />
                    <CardHeader className="p-4 pb-2">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn("text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded",
                          q.type === 'Behavioral' ? "bg-blue-950 text-blue-400" :
                            q.type === 'Technical' ? "bg-emerald-950 text-emerald-400" :
                              q.type === 'Red Flag' ? "bg-red-950 text-red-400" : "bg-purple-950 text-purple-400"
                        )}>{q.type}</span>
                      </div>
                      <CardTitle className="text-sm font-medium text-zinc-100 leading-snug">
                        {q.question}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-2 space-y-3 bg-black/20">
                      {q.context && (
                        <div className="text-xs text-zinc-500 bg-zinc-950/50 p-2 rounded border border-zinc-800/50 flex gap-2 items-start">
                          <MessageSquare className="w-3 h-3 mt-0.5 shrink-0" />
                          <span><strong className="text-zinc-400">Context:</strong> {q.context}</span>
                        </div>
                      )}
                      {q.expected_answer && (
                        <div className="text-xs text-emerald-500/80 bg-emerald-950/10 p-2 rounded border border-emerald-900/20 flex gap-2 items-start">
                          <CheckCircle2 className="w-3 h-3 mt-0.5 shrink-0" />
                          <span><strong className="text-emerald-500">Look for:</strong> {q.expected_answer}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}

                <div className="flex justify-end pt-4">
                  <Button variant="ghost" className="text-zinc-500 hover:text-white" onClick={() => setConfigOpen(true)}>
                    <Settings2 className="w-4 h-4 mr-2" /> Configure & Regenerate
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="chat" className="m-0 flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {chatHistory.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-4 opacity-50">
                  <Bot className="w-12 h-12" />
                  <p className="text-sm">Ask "The Investigator" anything about this candidate.</p>
                </div>
              ) : (
                chatHistory.map((msg, i) => (
                  <div key={i} className={cn("flex gap-3", msg.role === 'user' ? "flex-row-reverse" : "flex-row")}>
                    <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                      msg.role === 'user' ? "bg-zinc-800" : "bg-blue-900/50"
                    )}>
                      {msg.role === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 text-blue-400" />}
                    </div>
                    <div className={cn("rounded-lg p-3 text-sm max-w-[80%]",
                      msg.role === 'user' ? "bg-zinc-800 text-zinc-100" : "bg-blue-950/20 text-zinc-300 border border-blue-900/30"
                    )}>
                      {msg.role === 'user' ? (
                        msg.content
                      ) : (
                        <ReactMarkdown
                          components={{
                            ul: ({ ...props }) => <ul className="list-disc pl-4 space-y-1 my-2" {...props} />,
                            ol: ({ ...props }) => <ol className="list-decimal pl-4 space-y-1 my-2" {...props} />,
                            p: ({ ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                            h1: ({ ...props }) => <h1 className="text-lg font-bold mb-2" {...props} />,
                            h2: ({ ...props }) => <h2 className="text-base font-bold mb-2" {...props} />,
                            h3: ({ ...props }) => <h3 className="text-sm font-bold mb-1" {...props} />,
                            code: ({ ...props }) => <code className="bg-black/30 rounded px-1 py-0.5 font-mono text-xs" {...props} />,
                            pre: ({ ...props }) => <pre className="bg-black/30 rounded p-2 overflow-x-auto my-2 text-xs" {...props} />,
                            a: ({ ...props }) => <a className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      )}
                    </div>
                  </div>
                ))
              )}
              {chatWithCandidate.isPending && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-900/50 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-blue-400" />
                  </div>
                  <div className="bg-blue-950/20 rounded-lg p-3 border border-blue-900/30">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 bg-zinc-950 border-t border-zinc-800">
              <form
                className="flex gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <Input
                  value={messageInput}
                  onChange={e => setMessageInput(e.target.value)}
                  placeholder="Ask about skills, experience, or potential red flags..."
                  className="flex-1 bg-zinc-900 border-zinc-800"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className={cn(isRecording ? "text-red-500 bg-red-950/20" : "text-zinc-400")}
                  onClick={toggleRecording}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
                <Button type="submit" disabled={chatWithCandidate.isPending || !messageInput.trim()} size="icon">
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </TabsContent>

        </div>
      </Tabs>
    </div>
  );
}
