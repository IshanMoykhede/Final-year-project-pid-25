import React, { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { getMyFiles, preprocessDocument, viewFile } from '../api/files';
import type { FileData } from '../api/files';
import {
  analyzeClauseStep,
  getDocumentOverview,
  getOrderedClauses,
  initializeAnalysisSession,
} from '../api/analyzer';
import type {
  ClauseAnalysis,
  DocumentOverview,
  OrderedClauseItem,
  OrderedClauseListResponse,
} from '../api/analyzer';
import { askDocumentQuestion } from '../api/chat';
import type { RetrievedClause } from '../api/chat';
import { Button } from '../components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { DocumentChat } from '../components/documents/DocumentChat';
import { DocumentPdfViewer } from '../components/documents/DocumentPdfViewer';
import { AlertTriangle, ArrowLeft, FileText, Loader2, LocateFixed, MessageSquare, Sparkles } from 'lucide-react';

interface DocumentDetailProps {
  previewOnly?: boolean;
}

const getClauseAnalysisErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
      return detail.message;
    }
  }

  return error instanceof Error ? error.message : 'Unable to analyze this clause.';
};

export const DocumentDetail: React.FC<DocumentDetailProps> = ({ previewOnly = false }) => {
  const { fileId } = useParams<{ fileId: string }>();
  const [file, setFile] = useState<FileData | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [previewError, setPreviewError] = useState<string>('');
  const [isPreviewLoading, setIsPreviewLoading] = useState(true);
  const [overview, setOverview] = useState<DocumentOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [preprocessingMessage, setPreprocessingMessage] = useState('');
  const [error, setError] = useState('');
  const [selectedCitation, setSelectedCitation] = useState<RetrievedClause | null>(null);
  const [orderedClauses, setOrderedClauses] = useState<OrderedClauseItem[]>([]);
  const [analysisClause, setAnalysisClause] = useState<OrderedClauseItem | RetrievedClause | null>(null);
  const [clauseAnalysis, setClauseAnalysis] = useState<ClauseAnalysis | null>(null);
  const [isAnalyzingClause, setIsAnalyzingClause] = useState(false);
  const [clauseAnalysisError, setClauseAnalysisError] = useState('');
  const [citationError, setCitationError] = useState('');
  const [isLocatingCitation, setIsLocatingCitation] = useState(false);
  const [isInitializingSession, setIsInitializingSession] = useState(false);
  const [sessionSummary, setSessionSummary] = useState<OrderedClauseListResponse | null>(null);
  const [activeDocumentTab, setActiveDocumentTab] = useState<'chat' | 'analysis' | 'overview'>('overview');
  const analysisContentRef = useRef<HTMLDivElement>(null);
  const activeAnalysisChunkIdRef = useRef<string | null>(null);
  const citationCacheRef = useRef(new Map<string, RetrievedClause>());
  const citationRequestsRef = useRef(new Map<string, Promise<RetrievedClause>>());

  const rememberChatClauses = useCallback((clauses: RetrievedClause[]) => {
    clauses.forEach((clause) => {
      if (clause.bbox.length) citationCacheRef.current.set(clause.chunk_id, clause);
    });
  }, []);

  const resolveClauseCitation = (clause: OrderedClauseItem | RetrievedClause): Promise<RetrievedClause> => {
    const cachedCitation = citationCacheRef.current.get(clause.chunk_id);
    if (cachedCitation) return Promise.resolve(cachedCitation);
    if (!file) return Promise.reject(new Error('Document is not ready for citation lookup.'));

    const requestInFlight = citationRequestsRef.current.get(clause.chunk_id);
    if (requestInFlight) return requestInFlight;

    const clauseText = 'preview_text' in clause ? clause.preview_text : clause.text;
    const clauseLabel =
      'aliases' in clause && clause.aliases?.length
        ? clause.aliases.join(', ')
        : `Clause ${clause.chunk_no}`;
    const request = askDocumentQuestion({
      document_id: file.id,
      question: `Find the exact source text for ${clauseLabel}: ${clauseText}`,
      use_1hop_expansion: false,
    }).then((result) => {
      const citation = [...result.primary_clauses, ...result.expanded_clauses].find(
        (item) => item.chunk_id === clause.chunk_id
      );
      if (!citation?.bbox.length) {
        throw new Error('Location coordinates are not available for this clause.');
      }
      citationCacheRef.current.set(clause.chunk_id, citation);
      return citation;
    }).finally(() => {
      citationRequestsRef.current.delete(clause.chunk_id);
    });

    citationRequestsRef.current.set(clause.chunk_id, request);
    return request;
  };

  const prefetchClauseCitation = (clause: OrderedClauseItem) => {
    void resolveClauseCitation(clause).catch((citationRequestError: unknown) => {
      if (activeAnalysisChunkIdRef.current === clause.chunk_id) {
        setCitationError(`Citation is not ready yet: ${getClauseAnalysisErrorMessage(citationRequestError)}`);
      }
    });
  };

  useEffect(() => {
    if (activeDocumentTab === 'analysis' && analysisContentRef.current) {
      analysisContentRef.current.scrollTop = 0;
    }
  }, [activeDocumentTab, analysisClause]);

  const handleAnalyzeClause = async (clause: RetrievedClause) => {
    if (!file || isAnalyzingClause) return;

    const match = orderedClauses.find((item) => item.chunk_id === clause.chunk_id);
    const clauseTarget = match ?? {
      chunk_id: clause.chunk_id,
      chunk_no: clause.chunk_no,
      aliases: clause.aliases,
      status: 'PENDING',
      has_analysis: false,
      preview_text: clause.text,
    } as OrderedClauseItem;

    setActiveDocumentTab('analysis');
    if (clause.bbox.length) citationCacheRef.current.set(clause.chunk_id, clause);
    activeAnalysisChunkIdRef.current = clause.chunk_id;
    setSelectedCitation(clause.bbox.length ? clause : citationCacheRef.current.get(clause.chunk_id) ?? null);
    setCitationError('');
    setAnalysisClause(clauseTarget);
    setClauseAnalysis(null);
    setClauseAnalysisError('');
    setIsAnalyzingClause(true);

    try {
      const response = await analyzeClauseStep(clauseTarget.chunk_id, false);
      setClauseAnalysis(response.analysis);
      setOrderedClauses((current) =>
        current.map((item) =>
          item.chunk_id === clauseTarget.chunk_id
            ? { ...item, status: response.status, has_analysis: response.status === 'COMPLETED', risk_level: response.analysis.risk_level }
            : item
        )
      );
    } catch (analysisError) {
      setClauseAnalysisError(getClauseAnalysisErrorMessage(analysisError));
    } finally {
      setIsAnalyzingClause(false);
    }
  };

  const handleCiteAnalysisClause = async () => {
    if (!analysisClause || !file || isLocatingCitation) return;

    setCitationError('');
    activeAnalysisChunkIdRef.current = analysisClause.chunk_id;
    setIsLocatingCitation(true);
    try {
      const citation = await resolveClauseCitation(analysisClause);
      setSelectedCitation(citation);
    } catch (citationRequestError) {
      setCitationError(getClauseAnalysisErrorMessage(citationRequestError));
    } finally {
      setIsLocatingCitation(false);
    }
  };

  const handleInitializeClauseSession = async () => {
    if (!fileId) return;

    setIsInitializingSession(true);
    setClauseAnalysisError('');

    try {
      await initializeAnalysisSession(fileId);
      const ordered = await getOrderedClauses(fileId);
      setSessionSummary(ordered);
      setOrderedClauses(ordered.clauses);
      setAnalysisClause((current) => {
        if (!current) return ordered.clauses[0] ?? null;
        return ordered.clauses.find((item) => item.chunk_id === (current as OrderedClauseItem).chunk_id) ?? current;
      });
      if (ordered.clauses.length > 0) {
        setActiveDocumentTab('analysis');
      }
    } catch (initError) {
      setClauseAnalysisError(getClauseAnalysisErrorMessage(initError));
    } finally {
      setIsInitializingSession(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadDocument = async () => {
      if (!fileId) {
        setError('Document ID is missing.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError('');
        setPreviewError('');
        setPreviewUrl('');
        setIsPreviewLoading(true);

        const filesResponse = await getMyFiles();
        const fileMatch = filesResponse.data?.find((item) => item.id === fileId) ?? null;

        if (!isMounted) return;
        setFile(fileMatch);

        if (fileMatch) {
          try {
            const response = await viewFile(fileId);
            const rawContentType = response.headers?.['content-type'] ?? '';
            const contentType = Array.isArray(rawContentType) ? rawContentType[0] ?? '' : String(rawContentType);
            const blob = new Blob([response.data], {
              type: contentType || 'application/pdf',
            });

            if (String(fileMatch.content_type).includes('word') || contentType.includes('officedocument') || contentType.includes('zip')) {
              setPreviewError('DOCX preview is not supported in this viewer. Please download the file to view it.');
            } else if (contentType.includes('pdf') || String(fileMatch.content_type).includes('pdf')) {
              const objectUrl = URL.createObjectURL(blob);
              setPreviewUrl(objectUrl);
            } else {
              setPreviewError('This file type cannot be previewed in the browser.');
            }
          } catch (previewErr: any) {
            const message = previewErr.response?.data?.detail || previewErr.message || 'Unable to load the file preview.';
            setPreviewError(message);
          } finally {
            if (isMounted) setIsPreviewLoading(false);
          }
        } else {
          setPreviewError('This document could not be found.');
          setIsPreviewLoading(false);
        }

        if (!previewOnly) {
          if (fileMatch && fileMatch.status.toUpperCase() !== 'COMPLETED') {
            await preprocessDocument(fileId, (event) => {
              if (isMounted && event.status === 'processing') {
                setPreprocessingMessage(event.message || `Running ${event.step.toLowerCase()}...`);
              }
            });
            if (isMounted) setPreprocessingMessage('');
          }

          const overviewResponse = await getDocumentOverview(fileId);
          if (isMounted) setOverview(overviewResponse);

          try {
            const ordered = await getOrderedClauses(fileId);
            if (isMounted) {
              setSessionSummary(ordered);
              setOrderedClauses(ordered.clauses);
              if (ordered.clauses.length > 0) {
                setAnalysisClause(ordered.clauses[0]);
              }
            }
          } catch (orderedError) {
            if (isMounted) {
              setClauseAnalysisError(getClauseAnalysisErrorMessage(orderedError));
            }
          }
        }
      } catch (err: any) {
        if (isMounted) {
          const detail = err.response?.data?.detail;
          const message = typeof detail === 'string' ? detail : detail?.message;
          setError(message || err.message || 'Unable to load document details.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadDocument();

    return () => {
      isMounted = false;
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [fileId, previewOnly]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex items-center gap-3 text-gray-600">
          <Loader2 className="h-6 w-6 animate-spin text-accent" />
          <span>Loading document analysis...</span>
        </div>
      </div>
    );
  }

  if (error || !file) {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={() => window.history.back()} className="inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <Card>
          <CardContent className="p-6">
            <p className="text-red-600">{error || 'This document could not be found.'}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={previewOnly ? 'space-y-6' : 'flex min-h-0 flex-col gap-4'}>
      <div className="flex shrink-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">{previewOnly ? 'Document preview' : 'Document analysis'}</p>
          <h1 className="text-2xl font-bold text-gray-900">{file.file_name}</h1>
        </div>
        <Button
          variant="outline"
          onClick={() => (previewOnly ? window.close() : window.history.back())}
          className="inline-flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          {previewOnly ? 'Close preview' : 'Back to dashboard'}
        </Button>
      </div>

      {!previewOnly && preprocessingMessage && (
        <p className="shrink-0 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">{preprocessingMessage}</p>
      )}

      <div className={previewOnly ? 'flex justify-center' : 'min-h-0 flex-1'}>
        {previewOnly && <Card className="w-full max-w-5xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-accent" />
              File preview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isPreviewLoading ? (
              <div className="flex min-h-[320px] items-center justify-center gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
                <Loader2 className="h-5 w-5 animate-spin text-accent" />
                Loading preview...
              </div>
            ) : previewUrl ? (
              <div className="flex justify-center">
                <iframe
                  title={file.file_name}
                  src={previewUrl}
                  className="h-[calc(100vh-220px)] min-h-[520px] w-full max-w-4xl rounded-lg border border-gray-200 bg-white"
                />
              </div>
            ) : previewError ? (
              <div className="flex min-h-[320px] items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-600">
                {previewError}
              </div>
            ) : (
              <div className="flex min-h-[320px] items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
                No preview url is available for this document.
              </div>
            )}
          </CardContent>
        </Card>}

        {!previewOnly && <div className="grid min-h-0 grid-cols-1 gap-4 xl:h-[min(78vh,760px)] xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.9fr)]">
          <div className="min-h-0 min-w-0">
          <Card className="flex h-[min(70vh,680px)] min-h-[360px] flex-col overflow-hidden xl:h-full xl:min-h-0">
            <CardHeader className="shrink-0"><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5 text-accent" />Document preview</CardTitle></CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col overflow-hidden">
              {isPreviewLoading ? <div className="flex h-full min-h-[160px] items-center justify-center text-sm text-gray-500"><Loader2 className="mr-2 h-5 w-5 animate-spin text-accent" />Loading preview...</div> : previewUrl ? <DocumentPdfViewer url={previewUrl} selectedClause={selectedCitation} /> : <div className="flex h-full min-h-[160px] items-center justify-center rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-600">{previewError || 'No preview is available.'}</div>}
            </CardContent>
          </Card>

          </div>

          <div className="flex h-[min(70vh,680px)] min-h-[360px] min-w-0 flex-col gap-3 xl:h-full xl:min-h-0">
            <div className="grid shrink-0 grid-cols-3 rounded-xl border border-gray-200 bg-gray-50 p-1" role="tablist" aria-label="Document tools">
              <button
                type="button"
                role="tab"
                id="document-overview-tab"
                aria-selected={activeDocumentTab === 'overview'}
                aria-controls="document-overview-panel"
                onClick={() => setActiveDocumentTab('overview')}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  activeDocumentTab === 'overview' ? 'bg-white text-accent shadow-sm' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                <FileText className="h-4 w-4" />
                Overview
              </button>
              <button
                type="button"
                role="tab"
                id="document-chat-tab"
                aria-selected={activeDocumentTab === 'chat'}
                aria-controls="document-chat-panel"
                onClick={() => setActiveDocumentTab('chat')}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  activeDocumentTab === 'chat' ? 'bg-white text-accent shadow-sm' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                <MessageSquare className="h-4 w-4" />
                Chat
              </button>
              <button
                type="button"
                role="tab"
                id="clause-analysis-tab"
                aria-selected={activeDocumentTab === 'analysis'}
                aria-controls="clause-analysis-panel"
                onClick={() => setActiveDocumentTab('analysis')}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  activeDocumentTab === 'analysis' ? 'bg-white text-accent shadow-sm' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                <Sparkles className="h-4 w-4" />
                Clause analysis
              </button>
            </div>

            {activeDocumentTab === 'analysis' ? (
              <div
                id="clause-analysis-panel"
                role="tabpanel"
                aria-labelledby="clause-analysis-tab"
                className="min-h-0 flex-1 overflow-hidden"
              >
                <Card className="flex h-full min-h-0 flex-col overflow-hidden">
                  <CardHeader className="shrink-0 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-accent" />
                        Clause analysis
                      </CardTitle>
                      <div className="flex shrink-0 items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={isInitializingSession}
                          onClick={handleInitializeClauseSession}
                        >
                          {isInitializingSession ? 'Initializing...' : 'Start analysis'}
                        </Button>
                        {analysisClause && (
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={isLocatingCitation}
                            isLoading={isLocatingCitation}
                            onClick={handleCiteAnalysisClause}
                          >
                            <LocateFixed className="mr-1.5 h-4 w-4" />
                            Cite
                          </Button>
                        )}
                      </div>
                    </div>
                    {citationError && <p className="text-xs text-red-600" role="alert">{citationError}</p>}
                    {sessionSummary && (
                      <div className="flex flex-wrap gap-2 text-xs text-gray-600">
                        <span className="rounded-full bg-gray-100 px-2 py-1">{sessionSummary.total_clauses} clauses</span>
                        <span className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-700">{sessionSummary.completed} complete</span>
                        <span className="rounded-full bg-amber-100 px-2 py-1 text-amber-700">{sessionSummary.in_progress} in progress</span>
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700">{sessionSummary.pending} pending</span>
                      </div>
                    )}
                    {analysisClause && 'aliases' in analysisClause && Array.isArray(analysisClause.aliases) && analysisClause.aliases.length > 0 && (
                      <p className="text-sm text-gray-500">{analysisClause.aliases.join(', ')}</p>
                    )}
                    {analysisClause && 'chunk_no' in analysisClause && (!('aliases' in analysisClause) || !Array.isArray(analysisClause.aliases) || analysisClause.aliases.length === 0) && (
                      <p className="text-sm text-gray-500">Clause {analysisClause.chunk_no}</p>
                    )}
                  </CardHeader>
                  <CardContent ref={analysisContentRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain">
                    {orderedClauses.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-semibold text-gray-900">Clause review queue</h3>
                        </div>
                        <div className="grid max-h-40 grid-cols-2 gap-2 overflow-y-auto pr-1 sm:grid-cols-3">
                          {orderedClauses.map((clause) => {
                            const isActive = analysisClause && 'chunk_id' in analysisClause && clause.chunk_id === analysisClause.chunk_id;
                            const tone =
                              clause.status === 'COMPLETED'
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                                : clause.status === 'IN_PROGRESS'
                                  ? 'border-amber-200 bg-amber-50 text-amber-700'
                                  : 'border-slate-200 bg-slate-50 text-slate-700';

                            return (
                              <button
                                key={clause.chunk_id}
                                type="button"
                                onClick={async () => {
                                  if (analysisContentRef.current) {
                                    analysisContentRef.current.scrollTop = 0;
                                  }
                                  activeAnalysisChunkIdRef.current = clause.chunk_id;
                                  setAnalysisClause(clause);
                                  setClauseAnalysis(null);
                                  setClauseAnalysisError('');
                                  setCitationError('');
                                  setSelectedCitation(citationCacheRef.current.get(clause.chunk_id) ?? null);
                                  prefetchClauseCitation(clause);
                                  setIsAnalyzingClause(true);
                                  try {
                                    const response = await analyzeClauseStep(clause.chunk_id, false);
                                    setClauseAnalysis(response.analysis);
                                  } catch (analysisError) {
                                    setClauseAnalysisError(getClauseAnalysisErrorMessage(analysisError));
                                  } finally {
                                    setIsAnalyzingClause(false);
                                  }
                                }}
                                className={`rounded-lg border px-2 py-2 text-left text-xs font-medium transition ${tone} ${isActive ? 'ring-2 ring-accent/60' : ''}`}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <span>Clause {clause.chunk_no}</span>
                                  <span className="rounded-full bg-white/80 px-1.5 py-0.5 text-[10px] uppercase">{clause.status}</span>
                                </div>
                                {clause.aliases && clause.aliases.length > 0 && (
                                  <div className="mt-1 line-clamp-2 text-[10px] text-current/80">{clause.aliases.join(', ')}</div>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {!analysisClause ? (
                      <p className="text-sm text-gray-600">
                        Start the clause analysis session to review clauses serially and inspect each risk assessment here.
                      </p>
                    ) : isAnalyzingClause ? (
                      <div className="flex items-center gap-2 text-sm text-gray-600" role="status">
                        <Loader2 className="h-4 w-4 animate-spin text-accent" />
                        Analyzing clause and checking relevant context...
                      </div>
                    ) : clauseAnalysisError ? (
                      <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">{clauseAnalysisError}</p>
                    ) : clauseAnalysis ? (
                      <>
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-600" />
                          <span className="text-sm font-semibold text-gray-800">Risk level: {clauseAnalysis.risk_level}</span>
                        </div>
                        <section className="space-y-1">
                          <h3 className="text-sm font-semibold text-gray-900">In plain English</h3>
                          <p className="text-sm leading-relaxed text-gray-700">{clauseAnalysis.explanation}</p>
                        </section>
                        <section className="space-y-1">
                          <h3 className="text-sm font-semibold text-gray-900">Risk assessment</h3>
                          <p className="text-sm leading-relaxed text-gray-700">{clauseAnalysis.risk_analysis}</p>
                        </section>
                        {clauseAnalysis.entities_involved?.length > 0 && (
                          <section className="space-y-1">
                            <h3 className="text-sm font-semibold text-gray-900">Who is affected</h3>
                            <p className="text-sm text-gray-700">{clauseAnalysis.entities_involved.join(', ')}</p>
                          </section>
                        )}
                        {clauseAnalysis.real_world_examples?.length > 0 && (
                          <section className="space-y-1">
                            <h3 className="text-sm font-semibold text-gray-900">Practical examples</h3>
                            <ul className="list-disc space-y-1 pl-5 text-sm text-gray-700">
                              {clauseAnalysis.real_world_examples.map((example, index) => <li key={index}>{example}</li>)}
                            </ul>
                          </section>
                        )}
                        {clauseAnalysis.negotiation_advice && (
                          <section className="space-y-1">
                            <h3 className="text-sm font-semibold text-gray-900">Negotiation options</h3>
                            <p className="text-sm leading-relaxed text-gray-700">{clauseAnalysis.negotiation_advice}</p>
                          </section>
                        )}
                        {clauseAnalysis.faqs?.length > 0 && (
                          <section className="space-y-2">
                            <h3 className="text-sm font-semibold text-gray-900">Frequently asked questions</h3>
                            {clauseAnalysis.faqs.map((faq, index) => (
                              <div key={index} className="rounded-lg bg-gray-50 p-3">
                                <p className="text-sm font-medium text-gray-800">{faq.question}</p>
                                <p className="mt-1 text-sm text-gray-700">{faq.answer}</p>
                              </div>
                            ))}
                          </section>
                        )}
                        {clauseAnalysis.web_citations?.length > 0 && (
                          <section className="space-y-1">
                            <h3 className="text-sm font-semibold text-gray-900">Market references</h3>
                            <ul className="list-disc space-y-1 pl-5 text-sm">
                              {clauseAnalysis.web_citations.map((citation) => (
                                <li key={citation}>
                                  <a href={citation} target="_blank" rel="noreferrer" className="break-all text-accent underline">{citation}</a>
                                </li>
                              ))}
                            </ul>
                          </section>
                        )}
                      </>
                    ) : null}
                  </CardContent>
                </Card>
              </div>
            ) : activeDocumentTab === 'chat' ? (
              <div
                id="document-chat-panel"
                role="tabpanel"
                aria-labelledby="document-chat-tab"
                className="min-h-0 flex-1 overflow-hidden"
              >
                <DocumentChat
                  documentId={file.id}
                  onCitation={setSelectedCitation}
                  onClausesAvailable={rememberChatClauses}
                  onAnalyzeClause={handleAnalyzeClause}
                  isAnalyzingClause={isAnalyzingClause}
                />
              </div>
            ) : (
              <div
                id="document-overview-panel"
                role="tabpanel"
                aria-labelledby="document-overview-tab"
                className="min-h-0 flex-1 overflow-hidden"
              >
                {overview ? (
                  <Card className="flex h-full min-h-0 flex-col overflow-hidden">
                    <CardHeader className="shrink-0">
                      <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-accent" />
                        Document overview
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain text-sm text-gray-700">
                      <p>{overview.summary}</p>
                      <div className="grid gap-2 sm:grid-cols-3">
                        <div className="rounded bg-gray-50 p-2">
                          <span className="block text-xs text-gray-500">Type</span>
                          {overview.document_type}
                        </div>
                        <div className="rounded bg-gray-50 p-2">
                          <span className="block text-xs text-gray-500">Clauses</span>
                          {overview.total_clauses}
                        </div>
                        <div className="rounded bg-gray-50 p-2">
                          <span className="block text-xs text-gray-500">Jurisdiction</span>
                          {overview.jurisdiction}
                        </div>
                      </div>
                      {overview.parties.length > 0 && <p><strong>Parties:</strong> {overview.parties.join(', ')}</p>}
                      {overview.recommended_roadmap.length > 0 && (
                        <section className="space-y-2">
                          <h3 className="font-semibold text-gray-900">Recommended reading order</h3>
                          {overview.recommended_starting_point && (
                            <p className="text-xs text-gray-600">
                              Start with <strong>{overview.recommended_starting_point}</strong>
                              {overview.reasoning ? ` — ${overview.reasoning}` : ''}
                            </p>
                          )}
                          <ol className="list-decimal space-y-1 pl-5">
                            {overview.recommended_roadmap.map((category) => (
                              <li key={category}>{category}</li>
                            ))}
                          </ol>
                        </section>
                      )}
                      {overview.breakdown.length > 0 && (
                        <section className="space-y-2">
                          <h3 className="font-semibold text-gray-900">Clause breakdown</h3>
                          <ul className="space-y-1">
                            {overview.breakdown.map(({ category, count }) => (
                              <li key={category} className="flex justify-between gap-3">
                                <span>{category}</span>
                                <span className="font-mono text-gray-500">{count}</span>
                              </li>
                            ))}
                          </ul>
                        </section>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="h-full overflow-y-auto">
                    <CardContent className="p-4 text-sm text-gray-600">
                      Document overview is not available yet.
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>}
      </div>

    </div>
  );
};
