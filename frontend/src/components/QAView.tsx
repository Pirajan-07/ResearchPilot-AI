"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryDocument } from "@/lib/api";
import { Loader2, Send, BookOpen, User, Sparkles, CornerDownRight } from "lucide-react";
import { QueryResponse } from "@/types/analysis";

export function QAView({ documentId }: { documentId: string }) {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ q: string; a: QueryResponse | null; error: string | null; loading: boolean }[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const queryMutation = useMutation({
    mutationFn: (q: string) => queryDocument(documentId, q),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || queryMutation.isPending) return;

    const currentQ = question.trim();
    setQuestion("");
    
    setHistory(prev => [...prev, { q: currentQ, a: null, error: null, loading: true }]);
    
    try {
      const response = await queryMutation.mutateAsync(currentQ);
      setHistory(prev => prev.map((item, i) => 
        i === prev.length - 1 ? { ...item, a: response, loading: false } : item
      ));
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setHistory(prev => prev.map((item, i) => 
        i === prev.length - 1 ? { ...item, error: errorMessage, loading: false } : item
      ));
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div className="flex flex-col h-full bg-slate-50/30">
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-10 scroll-smooth"
      >
        {history.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
            <div className="w-16 h-16 bg-white rounded-2xl shadow-sm border border-slate-200 flex items-center justify-center mb-6">
              <Sparkles className="w-8 h-8 text-indigo-500" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Research Assistant</h3>
            <p className="text-slate-500">
              Ask specific questions about the methodology, findings, datasets, or any claims made in the uploaded research paper.
            </p>
          </div>
        ) : (
          history.map((item, idx) => (
            <div key={idx} className="space-y-6 max-w-4xl mx-auto w-full pb-6 border-b border-slate-100 last:border-0">
              {/* Question */}
              <div className="flex items-start gap-4">
                <div className="mt-1 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-slate-600" />
                </div>
                <div className="flex-1 pt-1.5">
                  <h4 className="text-base font-semibold text-slate-900">{item.q}</h4>
                </div>
              </div>
              
              {/* Answer */}
              <div className="flex items-start gap-4 pl-1 sm:pl-2">
                <div className="mt-1 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 border border-indigo-200">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="flex-1">
                  {item.loading ? (
                    <div className="flex items-center gap-3 text-slate-500 pt-2">
                      <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
                      <span className="text-sm font-medium">Scanning document and synthesizing answer...</span>
                    </div>
                  ) : item.error ? (
                    <div className="text-red-600 bg-red-50 p-4 rounded-lg border border-red-100 text-sm font-medium">
                      {item.error}
                    </div>
                  ) : item.a ? (
                    <div className="space-y-6">
                      <div className="prose prose-slate prose-sm sm:prose-base max-w-none text-slate-800 leading-relaxed">
                        <p>{item.a.answer}</p>
                      </div>
                      
                      {item.a.sources && item.a.sources.length > 0 && (
                        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mt-6">
                          <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-slate-500" />
                            <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Grounded Sources</h5>
                          </div>
                          <ul className="divide-y divide-slate-100">
                            {item.a.sources.map((src, i) => (
                              <li key={i} className="p-4 hover:bg-slate-50/50 transition-colors">
                                <div className="flex items-start gap-3 text-sm">
                                  <div className="shrink-0 flex flex-col items-center gap-1 mt-0.5">
                                    <span className="bg-indigo-50 text-indigo-700 border border-indigo-100 text-xs font-bold px-2 py-0.5 rounded">
                                      Page {src.page_number}
                                    </span>
                                  </div>
                                  <div className="flex-1 text-slate-600">
                                    <div className="flex items-start gap-2 mb-1">
                                      <CornerDownRight className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                                      <span className="italic leading-relaxed">&quot;{src.excerpt}&quot;</span>
                                    </div>
                                  </div>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 sm:p-6 bg-white border-t border-slate-200">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative flex items-end shadow-sm">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask about the methodology, claims, or data..."
              disabled={queryMutation.isPending}
              className="w-full bg-white border border-slate-300 text-slate-900 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 block pl-4 pr-14 py-3.5 min-h-[56px] max-h-32 resize-y text-base transition-colors"
              rows={1}
            />
            <div className="absolute right-2 bottom-2">
              <button 
                type="submit" 
                disabled={!question.trim() || queryMutation.isPending}
                className="p-2 text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:bg-slate-100 disabled:text-slate-400 transition-all shadow-sm flex items-center justify-center h-10 w-10"
                aria-label="Send question"
              >
                {queryMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5 ml-0.5" />
                )}
              </button>
            </div>
          </form>
          <div className="mt-2 text-center">
            <p className="text-[11px] text-slate-400 font-medium">ResearchPilot can make mistakes. Verify critical claims with the provided page citations.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
