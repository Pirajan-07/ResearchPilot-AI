"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSummary, fetchInsights } from "@/lib/api";
import { SummaryView } from "./SummaryView";
import { InsightsView } from "./InsightsView";
import { QAView } from "./QAView";
import { useState } from "react";
import { Loader2, AlertCircle, MessageSquare, FileText, Lightbulb } from "lucide-react";

export function DocumentAnalysis({ documentId }: { documentId: string }) {
  const [activeTab, setActiveTab] = useState<"qa" | "summary" | "insights">("qa");

  const { data: summary, isLoading: loadingSummary, error: errorSummary } = useQuery({
    queryKey: ["document", documentId, "summary"],
    queryFn: () => fetchSummary(documentId),
    enabled: !!documentId && activeTab === "summary",
    retry: false,
  });

  const { data: insights, isLoading: loadingInsights, error: errorInsights } = useQuery({
    queryKey: ["document", documentId, "insights"],
    queryFn: () => fetchInsights(documentId),
    enabled: !!documentId && activeTab === "insights",
    retry: false,
  });

  const renderContent = () => {
    if (activeTab === "qa") {
      return <QAView documentId={documentId} />;
    } else if (activeTab === "summary") {
      if (loadingSummary) return <LoadingState text="Generating Structured Summary..." />;
      if (errorSummary) return <ErrorState message={(errorSummary as Error).message} />;
      if (summary) return <SummaryView summary={summary} />;
      return <EmptyState text="No summary available." />;
    } else {
      if (loadingInsights) return <LoadingState text="Extracting Deep Insights..." />;
      if (errorInsights) return <ErrorState message={(errorInsights as Error).message} />;
      if (insights) return <InsightsView insights={insights} />;
      return <EmptyState text="No insights available." />;
    }
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden text-left flex flex-col h-full min-h-[700px]">
      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-slate-50/50 overflow-x-auto p-1.5 gap-1.5">
        <button
          onClick={() => setActiveTab("qa")}
          className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap ${
            activeTab === "qa"
              ? "bg-white text-indigo-700 shadow-sm border border-slate-200/60 ring-1 ring-slate-900/5"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-transparent"
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Interactive Q&A
        </button>
        <button
          onClick={() => setActiveTab("summary")}
          className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap ${
            activeTab === "summary"
              ? "bg-white text-indigo-700 shadow-sm border border-slate-200/60 ring-1 ring-slate-900/5"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-transparent"
          }`}
        >
          <FileText className="w-4 h-4" />
          Paper Summary
        </button>
        <button
          onClick={() => setActiveTab("insights")}
          className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap ${
            activeTab === "insights"
              ? "bg-white text-indigo-700 shadow-sm border border-slate-200/60 ring-1 ring-slate-900/5"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-transparent"
          }`}
        >
          <Lightbulb className="w-4 h-4" />
          Deep Insights
        </button>
      </div>

      <div className="flex-1 bg-white relative">
        {renderContent()}
      </div>
    </div>
  );
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 bg-white/80 backdrop-blur-sm z-10">
      <Loader2 className="h-8 w-8 animate-spin mb-4 text-indigo-500" />
      <p className="text-sm font-medium text-slate-700">{text}</p>
      <p className="text-xs text-slate-400 mt-2 max-w-xs text-center">
        This involves orchestrating context retrieval and LLM generation. It may take several seconds.
      </p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
      <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center text-center max-w-md shadow-sm">
        <AlertCircle className="h-10 w-10 mb-4 text-red-500" />
        <h3 className="text-base font-bold text-slate-900 mb-2">Generation Error</h3>
        <p className="text-sm font-medium text-red-700 leading-relaxed">{message}</p>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
      <p className="text-sm font-medium">{text}</p>
    </div>
  );
}
