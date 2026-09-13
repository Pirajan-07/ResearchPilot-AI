"use client";

import { useQuery } from "@tanstack/react-query";
import { getDocumentStatus } from "@/lib/api";
import { DocumentAnalysis } from "@/components/DocumentAnalysis";
import { Loader2, ArrowLeft, FileText, AlertCircle, CheckCircle2, Search, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { use } from "react";

export default function DocumentWorkspace({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const { data: document, isLoading, error } = useQuery({
    queryKey: ["document", id],
    queryFn: () => getDocumentStatus(id),
    refetchInterval: (query) => {
      const doc = query.state.data;
      if (!doc) return false;
      const isProcessing = doc.status === "extracting" || doc.status === "chunking" || doc.status === "uploaded";
      return isProcessing ? 3000 : false;
    },
  });

  const isProcessing = document?.status === "uploaded" || document?.status === "extracting" || document?.status === "chunking";
  const isFailed = document?.status === "failed";
  const isReady = document?.status === "completed";

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center shadow-sm">
              <Search className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 hidden sm:block">
              ResearchPilot
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            <Link 
              href="/"
              className="flex items-center text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Library
            </Link>
          </div>
        </div>
      </header>

      {/* Workspace Header */}
      <div className="bg-white border-b border-slate-200/60 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-start gap-4">
            <Link 
              href="/" 
              className="mt-1 p-1.5 -ml-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-100 transition-colors flex-shrink-0"
              aria-label="Back to Library"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2.5 mb-1.5">
                <h1 className="text-2xl font-bold text-slate-900 truncate tracking-tight" title={document?.filename || "Loading Document..."}>
                  {document?.filename || "Loading Document..."}
                </h1>
                
                {!isLoading && (
                  <span className="flex-shrink-0">
                    {isProcessing && (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Processing
                      </span>
                    )}
                    {isReady && (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Ready
                      </span>
                    )}
                    {isFailed && (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-700 bg-red-50 px-2.5 py-1 rounded-full border border-red-200">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Failed
                      </span>
                    )}
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-3 text-sm text-slate-500">
                {document && (
                  <>
                    <span className="flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-slate-400" />
                      {document.page_count} pages
                    </span>
                    <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                    <span>{document.chunk_count} chunks indexed</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-6" />
            <p className="text-lg font-medium text-slate-600">Loading workspace...</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-red-500">
            <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
            <h2 className="text-xl font-bold mb-2 text-slate-900">Error Loading Document</h2>
            <p className="text-slate-600 max-w-md text-center">{error.message}</p>
            <Link href="/" className="mt-8 px-6 py-2.5 bg-slate-100 text-slate-700 font-medium rounded-lg border border-slate-200 hover:bg-slate-200 transition-colors">
              Return to Library
            </Link>
          </div>
        ) : isProcessing ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 relative mb-8">
              <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <FileText className="w-8 h-8 text-indigo-500" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">Analyzing Document</h2>
            <p className="text-slate-500 max-w-md text-center mb-8">
              Extracting text and generating semantic embeddings. This prepares the document for deep insights and grounded Q&A.
            </p>
            
            <div className="w-full max-w-sm bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider">Processing Pipeline</h3>
              <div className="space-y-4">
                {document.stages.map((stage, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-slate-700 font-medium">{stage.name}</span>
                    {stage.status === "completed" ? (
                      <span className="text-emerald-600 font-semibold flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" /> Done
                      </span>
                    ) : stage.status === "running" ? (
                      <span className="text-amber-600 font-semibold flex items-center gap-1.5">
                        <Loader2 className="w-4 h-4 animate-spin" /> In Progress
                      </span>
                    ) : stage.status === "failed" ? (
                      <span className="text-red-600 font-semibold flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4" /> Failed
                      </span>
                    ) : (
                      <span className="text-slate-400 font-medium">Pending</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : isFailed ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-red-500">
            <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
            <h2 className="text-xl font-bold mb-2 text-slate-900">Processing Failed</h2>
            <p className="text-slate-600 max-w-md text-center bg-red-50 p-4 rounded-lg border border-red-100 mt-4">
              {document.error || "An unknown error occurred during document ingestion."}
            </p>
            <Link href="/" className="mt-8 px-6 py-2.5 bg-slate-100 text-slate-700 font-medium rounded-lg border border-slate-200 hover:bg-slate-200 transition-colors">
              Return to Library
            </Link>
          </div>
        ) : isReady ? (
          <div className="flex-1 w-full h-full pb-8">
            <DocumentAnalysis documentId={id} />
          </div>
        ) : null}
      </main>
    </div>
  );
}
