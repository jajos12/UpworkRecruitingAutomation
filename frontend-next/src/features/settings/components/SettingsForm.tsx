'use client';

import { useState, useEffect } from 'react';
import { useConfig, useUpdateConfig } from '../hooks/useSettings';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Lock, Save, Loader2, CheckCircle2, AlertCircle, Cpu, FileSpreadsheet, Briefcase } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function SettingsForm() {
  const { data: config, isLoading, isError } = useConfig();
  const updateConfig = useUpdateConfig();
  
  // AI State
  const [provider, setProvider] = useState<string>('openai');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  
  // Upwork State
  const [upworkClientId, setUpworkClientId] = useState('');
  const [upworkSecret, setUpworkSecret] = useState('');
  const [upworkToken, setUpworkToken] = useState('');

  // GCP State
  const [sheetId, setSheetId] = useState('');
  const [gcpJson, setGcpJson] = useState('');

  const [successMessage, setSuccessMessage] = useState('');

  // Sync state with loaded config
  useEffect(() => {
    if (config) {
      setProvider(config.ai_provider);
      // Set initial model based on provider
      if (config.ai_provider === 'openai') setModel(config.openai_model || '');
      else if (config.ai_provider === 'gemini') setModel(config.gemini_model || '');
      else if (config.ai_provider === 'claude') setModel(config.claude_model || '');
      
      setSheetId(config.google_sheet_id || '');
    }
  }, [config]);

  // Update model input when provider changes
  useEffect(() => {
    if (config) {
        if (provider === 'openai') setModel(config.openai_model || 'gpt-4-turbo-preview');
        else if (provider === 'gemini') setModel(config.gemini_model || 'gemini-1.5-pro-latest');
        else if (provider === 'claude') setModel(config.claude_model || 'claude-3-opus-20240229');
    }
  }, [provider, config]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage('');
    
    updateConfig.mutate(
      { 
        ai_provider: provider, 
        api_key: apiKey || undefined, 
        model_name: model,
        
        upwork_client_id: upworkClientId || undefined,
        upwork_client_secret: upworkSecret || undefined,
        upwork_access_token: upworkToken || undefined,
        
        google_sheet_id: sheetId || undefined,
        google_sheets_creds_json: gcpJson || undefined
      },
      {
        onSuccess: () => {
          setSuccessMessage('Configuration saved system updated.');
          // Clear sensitive fields
          setApiKey(''); 
          setUpworkClientId('');
          setUpworkSecret('');
          setUpworkToken('');
          setGcpJson('');
          setTimeout(() => setSuccessMessage(''), 5000);
        },
      }
    );
  };

  const hasKey = config ? (
    provider === 'openai' ? config.has_openai_key :
    provider === 'gemini' ? config.has_gemini_key :
    provider === 'claude' ? config.has_claude_key : false
  ) : false;

  if (isLoading) {
    return (
        <div className="flex items-center justify-center h-64">
           <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
        </div>
    );
  }

  if (isError) {
      return (
          <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>Failed to load configuration.</AlertDescription>
          </Alert>
      )
  }

  return (
    <Card className="bg-zinc-950 border-zinc-800 max-w-4xl mx-auto mt-8">
      <CardHeader>
        <CardTitle className="text-xl text-white flex items-center gap-2">
            Settings & Integrations
        </CardTitle>
        <CardDescription className="text-zinc-400">
          Configure external services and credentials.
        </CardDescription>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-6">
            {successMessage && (
                <Alert className="bg-emerald-950/50 border-emerald-900 text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertTitle>Success</AlertTitle>
                    <AlertDescription>{successMessage}</AlertDescription>
                </Alert>
            )}

            {updateConfig.isError && (
                 <Alert variant="destructive" className="bg-red-950/50 border-red-900 text-red-400">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>
                        {(updateConfig.error as any)?.response?.data?.detail || "Failed to update configuration."}
                    </AlertDescription>
                </Alert>
            )}

          <Tabs defaultValue="ai" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800 text-zinc-400 w-full justify-start h-12 p-1">
              <TabsTrigger value="ai" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white h-full px-6">
                 <Cpu className="w-4 h-4 mr-2" /> AI Provider
              </TabsTrigger>
              <TabsTrigger value="upwork" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white h-full px-6">
                 <Briefcase className="w-4 h-4 mr-2" /> Upwork API
              </TabsTrigger>
              <TabsTrigger value="google" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white h-full px-6">
                 <FileSpreadsheet className="w-4 h-4 mr-2" /> Google Sheets
              </TabsTrigger>
            </TabsList>
            
            {/* AI CONFIG TAB */}
            <TabsContent value="ai" className="mt-6 space-y-6">
                  <div className="space-y-2">
                    <Label className="text-zinc-300">AI Provider</Label>
                    <Select value={provider} onValueChange={setProvider}>
                      <SelectTrigger className="bg-zinc-900 border-zinc-800 text-white">
                        <SelectValue placeholder="Select a provider" />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                        <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                        <SelectItem value="gemini">Google Gemini 1.5</SelectItem>
                        <SelectItem value="claude">Anthropic Claude 3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-zinc-300">API Key</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                      <Input 
                        type="password" 
                        placeholder={hasKey ? "•••••••••••••••••••••••• (Configured)" : "Enter API Key"}
                        className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                      />
                    </div>
                     <p className="text-xs text-zinc-500">
                        {hasKey ? "API key is currently set. Enter a new one to update." : "An API key is required for this provider."}
                     </p>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-zinc-300">Model Name</Label>
                    <Input 
                      type="text" 
                      className="bg-zinc-900 border-zinc-800 text-white"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                    />
                    <p className="text-xs text-zinc-500">
                        Specific model identifier (e.g., gpt-4-turbo, gemini-1.5-pro, claude-3-opus-20240229)
                    </p>
                  </div>
            </TabsContent>

            {/* UPWORK CONFIG TAB */}
            <TabsContent value="upwork" className="mt-6 space-y-6">
                 <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg mb-4 text-sm text-zinc-400">
                   Requires Upwork API Client Credentials. Create one at <a href="https://www.upwork.com/api/keys/index.php" target="_blank" className="text-emerald-500 hover:underline">upwork.com/api</a>.
                 </div>

                 <div className="space-y-2">
                    <Label className="text-zinc-300">Client ID (Consumer Key)</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                      <Input 
                        type="password" 
                        placeholder={config?.has_upwork_client_id ? "•••••••••••••••• (Configured)" : "Enter Client ID"}
                        className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600"
                        value={upworkClientId}
                        onChange={(e) => setUpworkClientId(e.target.value)}
                      />
                    </div>
                 </div>

                 <div className="space-y-2">
                    <Label className="text-zinc-300">Client Secret</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                      <Input 
                        type="password" 
                        placeholder={config?.has_upwork_secret ? "•••••••••••••••• (Configured)" : "Enter Client Secret"}
                        className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600"
                        value={upworkSecret}
                        onChange={(e) => setUpworkSecret(e.target.value)}
                      />
                    </div>
                 </div>

                 <div className="space-y-2">
                    <Label className="text-zinc-300">OAuth Access Token (Optional / Manual)</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                      <Input 
                        type="password" 
                        placeholder={config?.has_upwork_token ? "•••••••••••••••• (Configured)" : "Enter Access Token"}
                        className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600"
                        value={upworkToken}
                        onChange={(e) => setUpworkToken(e.target.value)}
                      />
                    </div>
                    <p className="text-xs text-zinc-500">
                        If running locally without a callback server, provide a pre-generated token.
                    </p>
                 </div>
            </TabsContent>

            {/* GOOGLE SHEETS CONFIG TAB */}
            <TabsContent value="google" className="mt-6 space-y-6">
                 <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg mb-4 text-sm text-zinc-400">
                   1. Create a <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank" className="text-emerald-500 hover:underline">Service Account</a> in Google Cloud.<br/>
                   2. Download the JSON key file.<br/>
                   3. Paste the contents below.<br/>
                   4. Share your Master Sheet with the service account email.
                 </div>

                 <div className="space-y-2">
                    <Label className="text-zinc-300">Master Sheet ID</Label>
                    <Input 
                        placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                        className="bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600 font-mono"
                        value={sheetId}
                        onChange={(e) => setSheetId(e.target.value)}
                      />
                      <p className="text-xs text-zinc-500">Found in the URL of your Google Sheet.</p>
                 </div>

                 <div className="space-y-2">
                    <Label className="text-zinc-300">Service Account Credentials (JSON)</Label>
                    <div className="relative">
                        <Textarea 
                            placeholder={config?.has_google_creds ? "Credentials currently loaded. Paste new JSON to update." : "Paste contents of service-account.json here"}
                            className="bg-zinc-900 border-zinc-800 text-white font-mono text-xs min-h-[150px]"
                            value={gcpJson}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setGcpJson(e.target.value)}
                        />
                    </div>
                 </div>
            </TabsContent>

          </Tabs>

        </CardContent>
        <CardFooter className="border-t border-zinc-800 pt-6">
          <Button 
            type="submit" 
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
            disabled={updateConfig.isPending}
          >
            {updateConfig.isPending ? (
                <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                </>
            ) : (
                <>
                    <Save className="mr-2 h-4 w-4" /> Save Configuration
                </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
