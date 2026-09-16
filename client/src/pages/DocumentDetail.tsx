import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getMyFiles, preprocessDocument, viewFile } from '../api/files';
import type { FileData } from '../api/files';
import { getDocumentOverview } from '../api/analyzer';
import type { DocumentOverview } from '../api/analyzer';
import type { RetrievedClause } from '../api/chat';
import { Button } from '../components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { DocumentChat } from '../components/documents/DocumentChat';
import { RiskAnalysis } from '../components/documents/RiskAnalysis';
import { DocumentPdfViewer } from '../components/documents/DocumentPdfViewer';
import { ArrowLeft, FileText, Loader2, MessageSquare, Sparkles, AlertTriangle } from 'lucide-react';

interface DocumentDetailProps {
  previewOnly?: boolean;
}

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
  const [activeFeature, setActiveFeature] = useState<'chat' | 'risk'>('chat');
  const [selectedCitation, setSelectedCitation] = useState<RetrievedClause | null>(null);

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
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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

      <div className={previewOnly ? 'flex justify-center' : 'space-y-6'}>
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

        {!previewOnly && <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.9fr)]">
          <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5 text-accent" />Document preview</CardTitle></CardHeader>
            <CardContent>
              {isPreviewLoading ? <div className="flex min-h-[520px] items-center justify-center text-sm text-gray-500"><Loader2 className="mr-2 h-5 w-5 animate-spin text-accent" />Loading preview...</div> : previewUrl ? <DocumentPdfViewer url={previewUrl} selectedClause={selectedCitation} /> : <div className="flex min-h-[320px] items-center justify-center rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-600">{previewError || 'No preview is available.'}</div>}
            </CardContent>
          </Card>

          {overview && <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-accent" />Document overview</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-gray-700">
              <p>{overview.summary}</p>
              <div className="grid gap-2 sm:grid-cols-3"><div className="rounded bg-gray-50 p-2"><span className="block text-xs text-gray-500">Type</span>{overview.document_type}</div><div className="rounded bg-gray-50 p-2"><span className="block text-xs text-gray-500">Clauses</span>{overview.total_clauses}</div><div className="rounded bg-gray-50 p-2"><span className="block text-xs text-gray-500">Jurisdiction</span>{overview.jurisdiction}</div></div>
              {overview.parties.length > 0 && <p><strong>Parties:</strong> {overview.parties.join(', ')}</p>}
            </CardContent>
          </Card>}
          </div>

          <div className="min-w-0 space-y-4">
            <div className="flex rounded-xl border border-gray-200 bg-gray-50 p-1" role="tablist" aria-label="Document tools">
              <button type="button" role="tab" aria-selected={activeFeature === 'chat'} onClick={() => setActiveFeature('chat')} className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${activeFeature === 'chat' ? 'bg-white text-accent shadow-sm' : 'text-gray-500 hover:text-gray-900'}`}><MessageSquare className="h-4 w-4" />Chat</button>
              <button type="button" role="tab" aria-selected={activeFeature === 'risk'} onClick={() => setActiveFeature('risk')} className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${activeFeature === 'risk' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-900'}`}><AlertTriangle className="h-4 w-4" />Risk analysis</button>
            </div>
            {activeFeature === 'chat' ? <DocumentChat documentId={file.id} onCitation={setSelectedCitation} /> : <RiskAnalysis documentId={file.id} />}
          </div>
        </div>}
      </div>

      {!previewOnly && preprocessingMessage && (
        <p className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700">{preprocessingMessage}</p>
      )}


    </div>
  );
};
