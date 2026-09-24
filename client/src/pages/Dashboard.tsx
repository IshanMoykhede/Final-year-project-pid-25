import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyFiles, deleteFile } from '../api/files';
import type { FileData } from '../api/files';
import { FileUpload } from '../components/documents/FileUpload';
import { Button } from '../components/common/Button';
import { FileText, Trash2, Eye, File, Loader2, ScanEye } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [files, setFiles] = useState<FileData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const response = await getMyFiles();
      if (response.success && response.data) {
        setFiles(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch files', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleDelete = async (fileId: string) => {
    if (!window.confirm('Delete this contract and purge its audit trail? This cannot be undone.')) return;
    try {
      await deleteFile(fileId);
      setFiles((currentFiles) => currentFiles.filter((file) => file.id !== fileId));
    } catch (error) {
      console.error('Failed to delete file', error);
    }
  };

  const openPreview = (fileId: string) => {
    const previewWindow = window.open(`/document/${fileId}/preview`, '_blank', 'noopener,noreferrer');
    if (!previewWindow) {
      window.alert('Please allow pop-ups to open the document preview.');
    }
  };

  const getStatusBadge = (status: string) => {
    const norm = (status || '').toUpperCase();
    if (norm === 'COMPLETED' || norm === 'READY') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-olive-soft text-olive dark:text-emerald-300 border border-olive/30">
          Audited
        </span>
      );
    }
    if (norm === 'FAILED' || norm === 'NEEDS ATTENTION') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-crimson-soft text-crimson dark:text-rose-300 border border-crimson/30">
          Review Needed
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-soft text-amber-deep dark:text-amber-soft border border-amber/30">
        Parsing Layout
      </span>
    );
  };

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-2 border-b border-sand dark:border-stone-muted pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-mono font-semibold uppercase tracking-widest text-brass mb-1">
            STATUTORY REPOSITORY & BENCHMARKING
          </p>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-charcoal dark:text-ivory tracking-tight">
            Active Review Console
          </h1>
          <p className="mt-1 text-xs text-stone-muted dark:text-sand/80 font-sans">
            Contracts ingested into isolated graph stores with clause-level coordinate indexing.
          </p>
        </div>
      </div>

      {/* Metrics strip */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded border border-sand dark:border-stone-muted bg-surface dark:bg-stone p-5 shadow-subtle">
          <p className="text-xs font-mono uppercase text-muted">Audited Contracts</p>
          <p className="mt-2 font-display text-3xl font-bold text-charcoal dark:text-ivory">{files.length}</p>
        </div>
        <div className="rounded border border-sand dark:border-stone-muted bg-surface dark:bg-stone p-5 shadow-subtle">
          <p className="text-xs font-mono uppercase text-muted">Verified & Indexed</p>
          <p className="mt-2 font-display text-3xl font-bold text-charcoal dark:text-ivory">
            {files.filter((f) => f.status.toUpperCase() === 'COMPLETED').length}
          </p>
        </div>
        <div className="rounded border border-sand dark:border-stone-muted bg-surface dark:bg-stone p-5 shadow-subtle">
          <p className="text-xs font-mono uppercase text-muted">Awaiting Processing</p>
          <p className="mt-2 font-display text-3xl font-bold text-charcoal dark:text-ivory">
            {files.filter((f) => f.status.toUpperCase() !== 'COMPLETED').length}
          </p>
        </div>
      </div>

      {/* Upload Drop Zone */}
      <section>
        <div className="mb-3">
          <h2 className="font-display text-base font-bold text-charcoal dark:text-ivory">
            Ingest Agreement
          </h2>
        </div>
        <FileUpload onUploadSuccess={fetchFiles} />
      </section>

      {/* Document cards / table */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-base font-bold text-charcoal dark:text-ivory">
              Contract Inventory
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Select an agreement to launch the dual-pane review workspace or interrogate clauses.
            </p>
          </div>
          <span className="text-xs font-mono text-muted">{files.length} active</span>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 text-brass animate-spin" />
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-sand dark:border-stone-muted rounded bg-surface dark:bg-stone">
            <File className="w-10 h-10 text-muted mx-auto mb-3 stroke-[1.25]" />
            <p className="text-sm font-medium text-charcoal dark:text-ivory">
              No contracts loaded in this workspace.
            </p>
            <p className="text-xs text-muted mt-1">
              Upload an executed or draft agreement above to begin statutory review.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {files.map((file) => (
              <div
                key={file.id}
                className="rounded border border-sand dark:border-stone-muted bg-surface dark:bg-stone p-5 shadow-subtle hover:border-brass/50 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="w-9 h-9 rounded bg-parchment dark:bg-charcoal border border-sand dark:border-stone-muted flex items-center justify-center text-charcoal dark:text-ivory">
                      <FileText className="w-4 h-4 stroke-[1.5]" />
                    </div>
                    {getStatusBadge(file.status)}
                  </div>

                  <h3
                    className="font-display text-sm font-bold text-charcoal dark:text-ivory mb-1 truncate"
                    title={file.file_name}
                  >
                    {file.file_name}
                  </h3>

                  <div className="flex items-center gap-2 text-[11px] font-mono text-muted mb-5">
                    <span>PDF</span>
                    <span>•</span>
                    <span>{new Date(file.created_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-2 pt-3 border-t border-sand/70 dark:border-stone-muted/70 mt-auto">
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => openPreview(file.id)}>
                      <ScanEye className="w-3.5 h-3.5 mr-1 stroke-[1.5]" />
                      Preview
                    </Button>
                    <Link to={`/document/${file.id}`}>
                      <Button variant="brass" size="sm">
                        <Eye className="w-3.5 h-3.5 mr-1 stroke-[1.5]" />
                        Review Workspace
                      </Button>
                    </Link>
                  </div>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-1.5 text-muted hover:text-crimson hover:bg-crimson-soft rounded transition-colors cursor-pointer"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4 stroke-[1.5]" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
