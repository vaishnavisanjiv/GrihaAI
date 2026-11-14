'use client';

import { useState } from 'react';
import {
  MessageSquareText,
  Send,
  Loader2,
  Sparkles,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AssistantResponse } from './types';

interface AnalysisAssistantProps {
  onAsk: (question: string) => Promise<void>;
  response: AssistantResponse | null;
  isLoading: boolean;
  error?: string;
}

const PRESET_QUESTIONS = [
  'What are the main observations in this floor plan?',
  'How many rooms were detected?',
  'Which architectural elements were identified?',
  'Which relationships need review?',
  'Why are room dimensions not available?',
  'What should I verify next?',
];

export function AnalysisAssistant({
  onAsk,
  response,
  isLoading,
  error,
}: AnalysisAssistantProps) {
  const [inputQuestion, setInputQuestion] = useState(
    'What are the main observations in this floor plan?'
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isLoading) return;
    void onAsk(inputQuestion);
  };

  const handleChipClick = (question: string) => {
    setInputQuestion(question);
    void onAsk(question);
  };

  return (
    <Card className="border-slate-200 bg-white shadow-xs">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-3">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-2 text-base font-bold text-slate-900">
            <MessageSquareText className="h-4 w-4 text-cyan-600" />
            Ask BuildGuard Assistant
          </CardTitle>
          <span className="text-xs text-slate-500">
            Grounded in current plan detections & screening records
          </span>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Preset Question Chips */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Frequently Asked Screening Inquiries:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                disabled={isLoading}
                onClick={() => handleChipClick(q)}
                className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700 transition hover:border-cyan-300 hover:bg-cyan-50/50 hover:text-cyan-800 disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Question Form */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="Ask about room counts, detected elements, clearances, or next steps..."
            className="flex-1 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
          />
          <button
            type="submit"
            disabled={isLoading || !inputQuestion.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
            Ask
          </button>
        </form>

        {/* Error notification */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Assistant Response Card */}
        {response && (
          <div className="rounded-xl border border-cyan-100 bg-cyan-50/40 p-4 space-y-3 animate-in fade-in duration-150">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-cyan-800">
              <Sparkles className="h-3.5 w-3.5 text-cyan-600" />
              BuildGuard Response
            </div>

            <p className="text-xs leading-relaxed text-slate-700 whitespace-pre-line">
              {response.answer}
            </p>

            {/* Context chips */}
            {response.context && response.context.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Grounding Context:</span>
                {response.context.map((ctx, idx) => (
                  <span
                    key={idx}
                    className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-mono text-slate-600"
                  >
                    {ctx}
                  </span>
                ))}
              </div>
            )}

            {/* Suggested Follow-up Actions */}
            {response.suggested_actions && response.suggested_actions.length > 0 && (
              <div className="border-t border-cyan-100/80 pt-2.5 space-y-1.5">
                <span className="text-[10px] font-semibold text-cyan-900 uppercase tracking-wider">
                  Suggested Verification Actions:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {response.suggested_actions.map((action, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleChipClick(action)}
                      className="inline-flex items-center gap-1 rounded-md border border-cyan-200 bg-white px-2.5 py-1 text-xs text-cyan-800 hover:bg-cyan-50 transition"
                    >
                      <span>{action}</span>
                      <ArrowRight className="h-3 w-3 text-cyan-500" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
