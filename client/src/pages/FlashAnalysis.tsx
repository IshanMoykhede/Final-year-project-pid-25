import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  CircleHelp,
  FileText,
  Loader2,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { generateFlashAnalysis } from '../api/flashAnalysis';
import type { FlashAnalysisResponse } from '../api/flashAnalysis';
import { getMyFiles, preprocessDocument } from '../api/files';
import type { PreprocessEvent } from '../api/files';
import type { FileData } from '../api/files';
import { Button } from '../components/common/Button';
import { Card, CardContent } from '../components/common/Card';
import { Eyebrow } from '../components/common/Eyebrow';

const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
      return detail.message;
    }
  }

  return error instanceof Error ? error.message : 'Unable to generate the flash analysis.';
};

type ProgressStatus = 'idle' | 'preprocessing' | 'analyzing' | 'completed' | 'failed';

const PREPROCESS_STEPS = ['OCR', 'CHUNKING', 'CLASSIFICATION', 'EMBEDDING'];

export const FlashAnalysis: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const [file, setFile] = useState<FileData | null>(null);
  const [isLoadingFile, setIsLoadingFile] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressStatus, setProgressStatus] = useState<ProgressStatus>('idle');
  const [progressEvents, setProgressEvents] = useState<PreprocessEvent[]>([]);
  const [analysis, setAnalysis] = useState<FlashAnalysisResponse | null>(null);
  const [error, setError] = useState('');
  const completedPreprocessSteps = progressEvents.filter(
    (event) => PREPROCESS_STEPS.includes(event.step) && event.status === 'completed'
  ).length;
  const preprocessProgress = Math.round((completedPreprocessSteps / PREPROCESS_STEPS.length) * 100);
  const categories = analysis?.report.category_analysis ?? [];
  const warnings = analysis?.report.important_warnings ?? [];
  const nextSteps = analysis?.report.before_you_sign ?? [];

  useEffect(() => {
    let isMounted = true;

    const loadFile = async () => {
      if (!fileId) {
        setError('Document ID is missing.');
        setIsLoadingFile(false);
        return;
      }

      try {
        const response = await getMyFiles();
        const match = response.data?.find((item) => item.id === fileId) ?? null;
        if (isMounted) {
          setFile(match);
          if (!match) setError('This document could not be found in your workspace.');
        }
      } catch (loadError) {
        if (isMounted) setError(getErrorMessage(loadError));
      } finally {
        if (isMounted) setIsLoadingFile(false);
      }
    };

    void loadFile();
    return () => {
      isMounted = false;
    };
  }, [fileId]);

  const handleGenerate = async () => {
    if (!file || isGenerating) return;

    setError('');
    setIsGenerating(true);
    setProgressEvents([]);
    try {
      if (file.status.toUpperCase() !== 'COMPLETED') {
        setProgressStatus('preprocessing');
        await preprocessDocument(file.id, (event) => {
          setProgressEvents((current) => {
            const existingIndex = current.findIndex((item) => item.step === event.step);
            if (existingIndex < 0) return [...current, event];

            const next = [...current];
            next[existingIndex] = event;
            return next;
          });
        });
        const refreshedFiles = await getMyFiles();
        const refreshedFile = refreshedFiles.data?.find((item) => item.id === file.id);
        if (!refreshedFile) {
          throw new Error('Preprocessing finished, but the document status could not be retrieved.');
        }
        setFile(refreshedFile);
        if (refreshedFile.status.toUpperCase() !== 'COMPLETED') {
          throw new Error(`Preprocessing finished with document status "${refreshedFile.status}".`);
        }
      }

      setProgressStatus('analyzing');
      const result = await generateFlashAnalysis(file.id);
      setAnalysis(result);
      setProgressStatus('completed');
    } catch (generateError) {
      setError(getErrorMessage(generateError));
      setProgressStatus('failed');
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoadingFile) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-stone-muted">
        <Loader2 className="h-5 w-5 animate-spin text-brass-deep" />
        <span>Loading document details...</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 py-2 text-charcoal">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link to={fileId ? `/document/${fileId}` : '/dashboard'}>
          <Button variant="pill-outline" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to workspace
          </Button>
        </Link>
        <span className="inline-flex items-center gap-2 rounded-full border border-sand bg-surface px-3 py-1.5 font-mono text-[11px] text-muted">
          <Sparkles className="h-3.5 w-3.5 text-brass-deep" />
          Whole-document review
        </span>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-crimson/25 bg-crimson-soft/50 p-4 text-sm text-crimson-deep" role="alert">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {!file ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto mb-4 h-8 w-8 text-brass-deep" />
            <h1 className="font-display text-2xl text-charcoal">Document unavailable</h1>
            <p className="mt-2 text-sm text-stone-muted">Return to your workspace and select a document to review.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <section className="rounded-[32px] border border-sand bg-surface p-6 shadow-card sm:p-9">
            <Eyebrow>Flash Analysis</Eyebrow>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
              <div>
                <h1 className="font-display text-3xl font-normal leading-tight text-charcoal sm:text-4xl">
                  The whole agreement, understood in a flash.
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-muted">
                  Get a plain-English overview, key clause categories, important warnings, and practical questions to
                  consider before signing.
                </p>
                <div className="mt-6 flex items-center gap-2 rounded-2xl border border-sand bg-parchment-low px-4 py-3">
                  <FileText className="h-4 w-4 shrink-0 text-brass-deep" />
                  <p className="min-w-0 truncate text-sm font-medium text-charcoal" title={file.file_name}>
                    {file.file_name}
                  </p>
                </div>
              </div>
              <Button
                variant="brass"
                size="lg"
                className="gap-2"
                disabled={isGenerating}
                isLoading={isGenerating}
                onClick={handleGenerate}
              >
                {analysis ? <RefreshCw className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                {isGenerating
                  ? progressStatus === 'preprocessing' ? 'Preprocessing document...' : 'Reviewing document...'
                  : analysis ? 'Run again' : 'Generate analysis'}
              </Button>
            </div>
            {file.status.toUpperCase() !== 'COMPLETED' && (
              <p className="mt-4 text-xs text-amber-deep">
                The document will be preprocessed first. Live updates from the existing server progress stream will appear here.
              </p>
            )}
          </section>

          {progressStatus !== 'idle' && (
            <div
              className={`rounded-2xl border p-5 ${
                progressStatus === 'failed'
                  ? 'border-crimson/25 bg-crimson-soft/30'
                  : progressStatus === 'completed'
                    ? 'border-olive/25 bg-olive-soft'
                    : 'border-brass/25 bg-brass-subtle'
              }`}
              role={isGenerating ? 'status' : 'region'}
              aria-live="polite"
              aria-label="Backend processing progress"
            >
              <div className="flex items-start gap-4">
                {isGenerating ? (
                  <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-brass-deep" />
                ) : progressStatus === 'failed' ? (
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-crimson-deep" />
                ) : (
                  <CheckCircle2 className={`mt-0.5 h-5 w-5 shrink-0 ${progressStatus === 'completed' ? 'text-olive-deep' : 'text-brass-deep'}`} />
                )}
                <div>
                  <p className="text-sm font-medium text-charcoal">
                    {progressStatus === 'preprocessing'
                      ? 'Preprocessing document'
                      : progressStatus === 'analyzing'
                        ? 'Waiting for Flash Analysis response'
                        : progressStatus === 'completed'
                          ? 'Flash Analysis complete'
                          : progressStatus === 'failed'
                            ? 'Processing failed'
                            : ''}
                  </p>
                  <p className="mt-1 text-sm text-stone-muted">
                    {progressStatus === 'preprocessing'
                      ? `Backend preprocessing stages completed: ${completedPreprocessSteps} of ${PREPROCESS_STEPS.length}. This counts completed stages, not elapsed work within the current stage.`
                      : progressStatus === 'analyzing'
                          ? 'Request sent. Waiting for the backend response; it does not expose extraction or LLM substep progress.'
                        : progressStatus === 'completed'
                            ? `Backend returned the report for ${analysis?.chunk_count ?? 0} processed sections.`
                          : progressStatus === 'failed'
                            ? 'The backend request failed. Review the error and latest backend event below.'
                            : ''}
                  </p>
                </div>
              </div>

              {progressStatus === 'preprocessing' && (
                <div className="mt-5" aria-label="Preprocessing stage completion">
                  <div className="mb-2 flex items-center justify-between font-mono text-[11px] text-muted">
                    <span>Preprocessing stages</span>
                    <span>{completedPreprocessSteps}/{PREPROCESS_STEPS.length} complete ({preprocessProgress}%)</span>
                  </div>
                  <div
                    className="flex h-2 gap-1 overflow-hidden rounded-full bg-parchment"
                    role="progressbar"
                    aria-label="Completed backend preprocessing stages"
                    aria-valuemin={0}
                    aria-valuemax={PREPROCESS_STEPS.length}
                    aria-valuenow={completedPreprocessSteps}
                    aria-valuetext={`${completedPreprocessSteps} of ${PREPROCESS_STEPS.length} preprocessing stages completed`}
                  >
                    {PREPROCESS_STEPS.map((step) => {
                      const event = progressEvents.find((item) => item.step === step);
                      const isComplete = event?.status === 'completed';
                      const isFailed = event?.status === 'error';
                      const isActive = event?.status === 'processing';
                      return (
                          <span
                            key={step}
                            className={`h-full flex-1 transition-colors ${
                              isFailed
                                ? 'bg-crimson'
                                : isComplete
                                  ? 'bg-olive'
                                  : isActive
                                    ? 'bg-brass motion-safe:animate-pulse'
                                    : 'bg-sand'
                            }`}
                            aria-hidden="true"
                          />
                      );
                    })}
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] font-mono text-muted sm:grid-cols-4">
                    {PREPROCESS_STEPS.map((step) => {
                      const event = progressEvents.find((item) => item.step === step);
                      return (
                          <span key={step} className="truncate">
                            {step}: {event?.status ?? 'waiting'}
                          </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {progressStatus === 'analyzing' && (
                <div className="mt-5">
                  <div
                    className="h-2 overflow-hidden rounded-full bg-parchment"
                    role="progressbar"
                    aria-label="Flash Analysis request status"
                    aria-valuetext="Waiting for the backend response; percentage progress is not provided"
                  >
                    <div className="h-full w-1/3 rounded-full bg-brass motion-safe:animate-[flash-progress_1.6s_ease-in-out_infinite]" />
                  </div>
                  <p className="mt-2 text-right font-mono text-[10px] text-muted">
                    Percentage unavailable from backend
                  </p>
                </div>
              )}

              {progressStatus === 'completed' && (
                <div
                  className="mt-5 h-2 overflow-hidden rounded-full bg-olive"
                  role="progressbar"
                  aria-label="Flash Analysis request completed"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={100}
                />
              )}

              {progressEvents.length > 0 && (
                <ol className="mt-5 space-y-2 border-t border-brass/15 pt-4">
                  {progressEvents.map((event) => {
                    const completed = event.status === 'completed';
                    const failed = event.status === 'error';
                    return (
                      <li key={event.step} className="flex items-start gap-3 text-sm">
                        <span
                          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                            completed
                              ? 'bg-olive-soft text-olive-deep'
                              : failed
                                ? 'bg-crimson-soft text-crimson-deep'
                                : 'bg-parchment text-brass-deep'
                          }`}
                        >
                          {completed ? <CheckCircle2 className="h-3.5 w-3.5" /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                        </span>
                        <span className="min-w-0">
                          <span className="font-medium text-charcoal">
                            {event.step === 'HEARTBEAT' ? 'Backend heartbeat' : event.step}
                          </span>
                          <span className="ml-2 text-[11px] font-mono uppercase text-muted">{event.status}</span>
                          {event.message && <span className="mt-0.5 block text-stone-muted">{event.message}</span>}
                        </span>
                      </li>
                    );
                  })}
                </ol>
              )}
            </div>
          )}

          {analysis && (
            <div className="space-y-6">
              <section className="rounded-3xl border border-brass/30 bg-brass-subtle p-6 sm:p-8">
                <div className="flex items-start gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-brass/25 bg-surface text-brass-deep">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <Eyebrow className="mb-2">Overall verdict</Eyebrow>
                    <p className="font-display text-xl leading-relaxed text-charcoal sm:text-2xl">
                      {analysis.report.overall_verdict}
                    </p>
                  </div>
                </div>
              </section>

              <Card>
                <CardContent className="p-6 sm:p-8">
                  <Eyebrow>Document overview</Eyebrow>
                  <p className="whitespace-pre-line text-sm leading-7 text-stone">{analysis.report.document_overview}</p>
                  <p className="mt-5 border-t border-sand pt-4 font-mono text-[11px] text-muted">
                    Reviewed {analysis.chunk_count} processed document sections
                  </p>
                </CardContent>
              </Card>

              <section className="space-y-4">
                <div>
                  <Eyebrow>Clause-by-clause themes</Eyebrow>
                  <h2 className="font-display text-2xl text-charcoal">What the agreement covers</h2>
                </div>
                {categories.length ? (
                  <div className="grid gap-4 lg:grid-cols-2">
                    {categories.map((category, index) => (
                      <Card key={`${category.category}-${index}`} className="h-full">
                        <CardContent className="p-6">
                          <div className="flex items-start justify-between gap-4">
                            <h3 className="font-display text-lg text-charcoal">{category.category}</h3>
                            <span className="shrink-0 rounded-full border border-sand bg-parchment px-2.5 py-1 font-mono text-[10px] text-muted">
                              {index + 1}
                            </span>
                          </div>
                          <div className="mt-5 space-y-4 text-sm leading-6">
                            <div>
                              <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-brass-deep">Key clauses</p>
                              <p className="whitespace-pre-line text-stone">{category.key_clauses}</p>
                            </div>
                            <div className="grid gap-4 sm:grid-cols-2">
                              <div>
                                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-olive-deep">Favorable terms</p>
                                <p className="whitespace-pre-line text-stone">{category.favorable_terms}</p>
                              </div>
                              <div>
                                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-crimson-deep">Potential risks</p>
                                <p className="whitespace-pre-line text-stone">{category.risks}</p>
                              </div>
                            </div>
                            <div>
                              <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-brass-deep">Obligations</p>
                              <p className="whitespace-pre-line text-stone">{category.obligations}</p>
                            </div>
                            <div className="border-t border-sand pt-3">
                              <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted">References</p>
                              <p className="whitespace-pre-line text-xs leading-5 text-stone-muted">{category.clause_references}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <Card>
                    <CardContent className="p-6 text-sm text-stone-muted">
                      No applicable clause categories were identified in this report.
                    </CardContent>
                  </Card>
                )}
              </section>

              <section className="space-y-4">
                <div>
                  <Eyebrow>Prioritized for your attention</Eyebrow>
                  <h2 className="font-display text-2xl text-charcoal">Important warnings</h2>
                </div>
                {warnings.length ? (
                  <div className="space-y-3">
                    {warnings.map((warning, index) => (
                      <div key={`${warning.title}-${index}`} className="flex gap-4 rounded-2xl border border-crimson/20 bg-crimson-soft/30 p-5">
                        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-crimson" />
                        <div>
                          <h3 className="font-medium text-charcoal">{warning.title}</h3>
                          <p className="mt-1 text-sm leading-6 text-stone">{warning.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex gap-3 rounded-2xl border border-olive/25 bg-olive-soft p-5 text-sm text-olive-deep">
                    <CheckCircle2 className="h-5 w-5 shrink-0" />
                    No specific warnings were returned in this analysis.
                  </div>
                )}
              </section>

              <section className="rounded-3xl border border-sand bg-surface p-6 shadow-subtle sm:p-8">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-parchment text-brass-deep">
                    <ListChecks className="h-5 w-5" />
                  </div>
                  <div>
                    <Eyebrow className="mb-1">Practical next steps</Eyebrow>
                    <h2 className="font-display text-2xl text-charcoal">Before you sign</h2>
                  </div>
                </div>
                {nextSteps.length ? (
                  <ol className="mt-6 space-y-3">
                    {nextSteps.map((action, index) => (
                      <li key={`${action}-${index}`} className="flex items-start gap-3 text-sm leading-6 text-stone">
                        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-sand bg-parchment font-mono text-[11px] text-brass-deep">
                          {index + 1}
                        </span>
                        {action}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="mt-5 text-sm text-stone-muted">No next steps were returned in this analysis.</p>
                )}
              </section>

              <div className="flex items-start gap-3 rounded-2xl border border-sand bg-parchment-low p-4 text-xs leading-5 text-stone-muted">
                <CircleHelp className="mt-0.5 h-4 w-4 shrink-0 text-brass-deep" />
                <p>
                  This AI-generated report is based on the processed document text and is intended to help you review
                  the agreement. Check important findings against the original document.
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
