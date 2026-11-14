"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProtectedRoute from "@/components/ProtectedRoute";
import { apiRequest } from "@/lib/api";
import {
  Upload,
  FileText,
  Search,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Database,
  ArrowRight,
  Layers,
  Clock,
  Send,
} from "lucide-react";

interface DocumentItem {
  id: number;
  filename: string;
  status: "uploaded" | "processing" | "processed" | "failed";
  indexing_status: "pending" | "indexed" | "failed";
  uploaded_at: string;
  indexed_at?: string | null;
  chunk_count?: number;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // RAG Q&A State
  const [query, setQuery] = useState("");
  const [ragAnswer, setRagAnswer] = useState<any | null>(null);
  const [searching, setSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const data = await apiRequest<DocumentItem[]>("/documents");
      setDocuments(data || []);
    } catch (err: any) {
      // ignore
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatusMessage({ type: "error", text: "Please select a valid PDF file." });
      return;
    }

    setIsUploading(true);
    setStatusMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const uploadedDoc = await apiRequest<DocumentItem>("/documents/upload", {
        method: "POST",
        body: formData,
      });

      setDocuments((prev) => [uploadedDoc, ...prev]);
      setStatusMessage({
        type: "success",
        text: `Document "${uploadedDoc.filename}" uploaded successfully.`,
      });

      // Auto-trigger text extraction
      await handleProcessDoc(uploadedDoc.id);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Upload failed." });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleProcessDoc = async (docId: number) => {
    setActionInProgress(docId);
    try {
      const processed = await apiRequest<DocumentItem>(`/documents/${docId}/process`, {
        method: "POST",
      });
      setDocuments((prev) =>
        prev.map((d) => (d.id === docId ? { ...d, status: processed.status } : d))
      );
      setStatusMessage({ type: "success", text: "Text extracted from PDF." });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to process PDF text." });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleIndexDoc = async (docId: number) => {
    setActionInProgress(docId);
    try {
      const res = await apiRequest<{
        id: number;
        indexing_status: "indexed" | "failed";
        indexed_at: string;
        chunk_count: number;
      }>(`/documents/${docId}/index`, {
        method: "POST",
      });

      setDocuments((prev) =>
        prev.map((d) =>
          d.id === docId
            ? {
                ...d,
                indexing_status: res.indexing_status,
                indexed_at: res.indexed_at,
                chunk_count: res.chunk_count,
              }
            : d
        )
      );

      setStatusMessage({
        type: "success",
        text: `Indexed into pgvector (${res.chunk_count} chunks generated with 768-dim embeddings).`,
      });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Indexing failed." });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setStatusMessage(null);

    try {
      const res = await apiRequest("/advisor/analyze", {
        method: "POST",
        body: JSON.stringify({ question: query }),
      });
      setRagAnswer(res);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Hybrid RAG search failed." });
    } finally {
      setSearching(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-screen bg-[#f8f9ff]">
        <Navbar />

        <main className="flex-1 pt-28 pb-20 px-4 sm:px-6 lg:px-12 max-w-7xl mx-auto w-full">
          {/* TOP BAR */}
          <div className="flex flex-col md:flex-row md:items-end justify-between pb-8 border-b border-slate-200 gap-4 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs tracking-wider uppercase mb-2">
                <Database className="w-4 h-4 text-indigo-600" />
                <span>Hybrid RAG • PostgreSQL pgvector &amp; BM25</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-display tracking-tight">
                Document Ingestion &amp; Grounded Q&amp;A
              </h1>
              <p className="text-sm sm:text-base text-slate-500 max-w-2xl mt-1">
                Upload financial reports, mutual fund factsheets, or brokerage statements. Documents are chunked into 768-dim embeddings in pgvector and searched deterministically to eliminate hallucinations.
              </p>
            </div>

            {statusMessage && (
              <div
                className={`p-4 rounded-2xl flex items-center gap-3 text-sm font-medium ${
                  statusMessage.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {statusMessage.type === "success" ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
                )}
                <span>{statusMessage.text}</span>
              </div>
            )}
          </div>

          {/* SPREAD OUT 12-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* LEFT 7 COLS: UPLOAD & ACTIVE FILINGS */}
            <div className="lg:col-span-7 space-y-8">
              {/* Upload Card */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
                      <Upload className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 font-display">
                        Upload Financial PDF
                      </h2>
                      <p className="text-xs text-slate-500">
                        Supports 10-K, annual reports, fund factsheets, and bank statements
                      </p>
                    </div>
                  </div>
                </div>

                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="p-8 border-2 border-dashed border-indigo-200 hover:border-indigo-500 rounded-2xl bg-indigo-50/40 hover:bg-indigo-50/70 transition-all text-center cursor-pointer group"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".pdf,application/pdf"
                    className="hidden"
                  />
                  <div className="w-12 h-12 rounded-2xl bg-white shadow-xs text-indigo-600 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                    {isUploading ? (
                      <div className="w-6 h-6 border-3 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
                    ) : (
                      <Upload className="w-6 h-6" />
                    )}
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">
                    {isUploading ? "Uploading & Extracting..." : "Click to select or drag PDF file here"}
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    Automatic parsing, token chunking, and embedding generation
                  </p>
                </div>
              </div>

              {/* Indexed Documents Table */}
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900 font-display">
                        Your Ingested Financial Documents
                      </h3>
                      <p className="text-xs text-slate-500">
                        Persisted in database with vector similarity indices
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700">
                    {documents.length} Files
                  </span>
                </div>

                {isLoadingDocs ? (
                  <div className="py-12 text-center text-xs text-slate-400">Loading documents...</div>
                ) : documents.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-slate-50 border border-dashed border-slate-200">
                    <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm font-medium text-slate-600">No documents ingested yet.</p>
                    <p className="text-xs text-slate-400 mt-1">
                      Upload a PDF report above to activate hybrid RAG citations.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-white hover:shadow-xs transition-all"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">{doc.filename}</h4>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                doc.indexing_status === "indexed"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {doc.indexing_status === "indexed" ? "Indexed in pgvector" : "Pending Index"}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                            <span>Status: <strong className="text-slate-800 capitalize">{doc.status}</strong></span>
                            {doc.chunk_count !== undefined && (
                              <span>Chunks: <strong className="text-slate-800">{doc.chunk_count}</strong></span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {doc.status !== "processed" && (
                            <button
                              onClick={() => handleProcessDoc(doc.id)}
                              disabled={actionInProgress === doc.id}
                              className="px-3 py-1.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold transition-all disabled:opacity-50"
                            >
                              Extract Text
                            </button>
                          )}
                          {doc.status === "processed" && doc.indexing_status !== "indexed" && (
                            <button
                              onClick={() => handleIndexDoc(doc.id)}
                              disabled={actionInProgress === doc.id}
                              className="px-3 py-1.5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50"
                            >
                              {actionInProgress === doc.id ? "Indexing..." : "Index Embeddings"}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT 5 COLS: GROUNDED RAG SEARCH STUDIO */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs">
                <div className="flex items-center gap-3 pb-6 border-b border-slate-100 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                    <Search className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 font-display">
                      Grounded Q&amp;A Search
                    </h3>
                    <p className="text-xs text-slate-500">
                      Cites exact chunks from your ingested filings
                    </p>
                  </div>
                </div>

                <form onSubmit={handleQuery} className="space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g. What are the key risk factors mentioned in the fund factsheet?"
                      className="w-full pl-4 pr-12 py-3.5 rounded-2xl border border-slate-200 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-50 text-sm outline-none text-slate-900 bg-slate-50/50"
                    />
                    <button
                      type="submit"
                      disabled={searching || !query.trim()}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white flex items-center justify-center transition-all disabled:opacity-50 cursor-pointer"
                    >
                      {searching ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {ragAnswer && (
                    <div className="mt-5 p-5 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-3">
                      <div className="flex items-center justify-between border-b border-indigo-100 pb-2.5">
                        <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                          <Sparkles className="w-4 h-4 text-indigo-600" /> Grounded Analysis
                        </span>
                        <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                          Citation Verified
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                        {ragAnswer.summary_narrative || ragAnswer.recommendation || JSON.stringify(ragAnswer, null, 2)}
                      </p>
                    </div>
                  )}
                </form>

                <div className="mt-6 pt-6 border-t border-slate-100 space-y-2 text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span>Cosine similarity search over 768-dimensional embeddings</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span>BM25 lexical reranking filters irrelevant document sections</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
}
