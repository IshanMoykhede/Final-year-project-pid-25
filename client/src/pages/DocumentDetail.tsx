import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getMyFiles, processDocument, viewFile } from '../api/files';
import type { FileData } from '../api/files';
import { Button } from '../components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';
import { ArrowLeft, FileText, Loader2, ShieldAlert, Sparkles } from 'lucide-react';

interface AnalysisResult {
  markdown: string;
  text: string;
  raw_llama_json: unknown[];
}

interface DocumentDetailProps {
  previewOnly?: boolean;
}

export const DocumentDetail: React.FC<DocumentDetailProps> = ({ previewOnly = false }) => {
  const { fileId } = useParams<{ fileId: string }>();
  const [file, setFile] = useState<FileData | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [previewError, setPreviewError] = useState<string>('');
  const [isPreviewLoading, setIsPreviewLoading] = useState(true);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

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
            const rawContentType = response.headers?.['content-type'] ?? response.headers?.['Content-Type'] ?? '';
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
          const analysisResponse = await processDocument(fileId);
          if (isMounted && analysisResponse?.data) {
            setAnalysis(analysisResponse.data);
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

      <div className={previewOnly ? 'flex justify-center' : 'grid gap-6 xl:grid-cols-[1.3fr_0.7fr]'}>
        <Card className={previewOnly ? 'w-full max-w-5xl' : undefined}>
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
        </Card>

        {!previewOnly && <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-amber-500" />
                Document status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-gray-700">
              <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                <span>Status</span>
                <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 capitalize">{file.status}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                <span>Uploaded</span>
                <span>{file.created_at ? new Date(file.created_at).toLocaleDateString() : 'Unknown'}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                <span>Type</span>
                <span>{file.content_type || 'Unknown'}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-accent" />
                AI extraction
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-gray-700">
              {analysis ? (
                <>
                  <p className="rounded-lg bg-accent/5 p-3 text-gray-700">
                    {analysis.text ? analysis.text.slice(0, 220) : 'No text extracted yet.'}
                    {analysis.text && analysis.text.length > 220 ? '...' : ''}
                  </p>
                  {analysis.raw_llama_json?.length ? (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                      <p className="mb-2 font-medium text-gray-800">Parsed items</p>
                      <ul className="list-inside list-disc space-y-1 text-xs text-gray-600">
                        {analysis.raw_llama_json.slice(0, 5).map((item, index) => (
                          <li key={`${(item as any)?.id ?? index}`}>
                            {(item as any)?.label || (item as any)?.title || 'Extracted content'}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="text-gray-500">No AI extraction has been generated yet for this document.</p>
              )}
            </CardContent>
          </Card>
        </div>}
      </div>

      {!previewOnly && <Card>
        <CardHeader>
          <CardTitle>Document markdown</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-slate max-w-none px-6 pb-6">
          {analysis?.markdown ? (
            <ReactMarkdown>{analysis.markdown}</ReactMarkdown>
          ) : (
            <p className="text-gray-500">No markdown content is available yet.</p>
          )}
        </CardContent>
      </Card>}
    </div>
  );
};
