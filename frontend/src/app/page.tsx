"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDocuments, uploadDocument, deleteDocument } from "@/lib/api";
import { Loader2, UploadCloud, FileText, Trash2, AlertCircle, CheckCircle2, XCircle, Search, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { DocumentStatusResponse } from "@/types/analysis";

export default function Home() {
  const queryClient = useQueryClient();
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const data = query.state.data as DocumentStatusResponse[] | undefined;
      if (!data) return false;
      const hasProcessing = data.some(
        (doc) => doc.status === "extracting" || doc.status === "chunking" || doc.status === "uploaded"
      );
      return hasProcessing ? 3000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => {
      setUploadError(err.message);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type !== "application/pdf") {
        setUploadError("Only PDF files are supported.");
        return;
      }
      uploadMutation.mutate(file);
      e.target.value = "";
    }
  };

  const handleDelete = (e: React.MouseEvent, docId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this document?")) {
      deleteMutation.mutate(docId);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center shadow-sm">
              <Search className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              ResearchPilot
            </h1>
          </div>
          <div className="flex items-center text-sm font-medium text-slate-500">
            <LayoutDashboard className="w-4 h-4 mr-2" />
            Workspace
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex flex-col gap-8">
        
        {/* Upload Section */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-slate-900">Upload Research Paper</h2>
            <p className="text-sm text-slate-500 mt-1 max-w-lg">
              Upload a PDF to automatically extract contents, generate semantic embeddings, and prepare the document for grounded Q&A, structured summary, and deep insights.
            </p>
          </div>
          <div className="w-full sm:w-auto relative group">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={handleFileChange} 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              disabled={uploadMutation.isPending}
              aria-label="Upload PDF document"
            />
            <button 
              className={`w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 font-medium rounded-lg transition-all shadow-sm
                ${uploadMutation.isPending 
                  ? 'bg-indigo-50 text-indigo-400 cursor-not-allowed border border-indigo-100' 
                  : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow group-hover:ring-4 ring-indigo-600/20'}`}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
              {uploadMutation.isPending ? 'Uploading...' : 'Select PDF File'}
            </button>
          </div>
        </section>

        {/* Error Banner */}
        {uploadError && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-start gap-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <p>{uploadError}</p>
          </div>
        )}

        {/* Library Section */}
        <section className="flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-900 tracking-tight">Document Library</h2>
            {documents && documents.length > 0 && (
              <span className="text-sm font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
                {documents.length} {documents.length === 1 ? 'Document' : 'Documents'}
              </span>
            )}
          </div>

          {isLoading ? (
            <div className="flex-1 flex justify-center items-center py-24 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-16 bg-white rounded-xl border border-slate-200 text-slate-600 shadow-sm">
              <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
              <p className="font-medium text-slate-900">Failed to load library</p>
              <p className="text-sm mt-1">Please ensure the backend service is running.</p>
            </div>
          ) : !documents || documents.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 bg-white border border-slate-200 border-dashed rounded-xl shadow-sm text-center">
              <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-slate-300" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">No documents found</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-sm">
                Your workspace is empty. Upload a research paper above to begin your analysis.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {documents.map((doc) => {
                const isProcessing = doc.status === "uploaded" || doc.status === "extracting" || doc.status === "chunking";
                const isFailed = doc.status === "failed";
                const isReady = doc.status === "completed";

                return (
                  <Link 
                    href={isReady ? `/documents/${doc.document_id}` : '#'} 
                    key={doc.document_id}
                    className={`block relative group bg-white rounded-xl border p-5 transition-all duration-200 flex flex-col h-full
                      ${isReady ? 'border-slate-200 hover:border-indigo-300 hover:shadow-md cursor-pointer' : 
                      isFailed ? 'border-red-100 bg-red-50/30 cursor-default' : 
                      'border-slate-200 bg-slate-50/50 cursor-default'}`}
                    onClick={(e) => { if (!isReady) e.preventDefault(); }}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className={`p-2.5 rounded-lg ${isReady ? 'bg-indigo-50 text-indigo-600' : isFailed ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-500'}`}>
                        <FileText className="w-5 h-5" />
                      </div>
                      
                      <button 
                        onClick={(e) => handleDelete(e, doc.document_id)}
                        className="text-slate-400 hover:text-red-600 p-1.5 rounded-md hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title="Delete document"
                        aria-label="Delete document"
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 text-base leading-snug line-clamp-2 mb-2" title={doc.filename}>
                        {doc.filename}
                      </h3>
                      
                      {isReady && (
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span>{doc.page_count} pages</span>
                          <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                          <span>{doc.chunk_count} chunks</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-slate-100/80 flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-medium">
                        {isProcessing && (
                          <span className="flex items-center gap-1.5 text-amber-600 bg-amber-50 px-2 py-1 rounded border border-amber-100">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Processing
                          </span>
                        )}
                        {isReady && (
                          <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-100">
                            <CheckCircle2 className="w-3 h-3" />
                            Ready
                          </span>
                        )}
                        {isFailed && (
                          <span className="flex items-center gap-1.5 text-red-600 bg-red-50 px-2 py-1 rounded border border-red-100 truncate max-w-[150px]" title={doc.error || 'Failed'}>
                            <XCircle className="w-3 h-3 shrink-0" />
                            Failed
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
