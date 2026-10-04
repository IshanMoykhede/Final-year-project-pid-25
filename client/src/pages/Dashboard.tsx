import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyFiles, deleteFile } from '../api/files';
import type { FileData } from '../api/files';
import { FileUpload } from '../components/documents/FileUpload';
import { Button } from '../components/common/Button';
import { Eyebrow } from '../components/common/Eyebrow';
import { FileText, Trash2, Eye, File, ScanEye } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

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
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-olive-soft text-olive border border-olive/30">
          Audited
        </span>
      );
    }
    if (norm === 'FAILED' || norm === 'NEEDS ATTENTION') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-crimson-soft text-crimson border border-crimson/30">
          Review Needed
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-amber-soft/50 text-amber-deep border border-amber/30">
        Parsing Layout
      </span>
    );
  };

  return (
    <div className="p-6 lg:p-8 space-y-10 max-w-7xl mx-auto text-charcoal">
      {/* Header */}
      <section className="px-4 py-6 sm:px-8 rounded-[40px] bg-surface border border-sand shadow-card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Eyebrow>Statutory Repository & Benchmarking</Eyebrow>
          <h1 className="font-display text-2xl sm:text-3xl font-normal text-charcoal">
            Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'}.
          </h1>
          <p className="mt-2 text-sm text-stone-muted font-sans max-w-lg">
            Contracts ingested into isolated graph stores with clause-level coordinate indexing.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-sand bg-parchment px-4 py-2">
           <span className="relative flex h-2 w-2">
             <span className="absolute inline-flex h-full w-full rounded-full bg-olive opacity-75 motion-safe:animate-ping" />
             <span className="relative inline-flex h-2 w-2 rounded-full bg-olive" />
           </span>
           <span className="font-mono text-xs text-muted">Workspace active</span>
        </div>
      </section>

      {/* Metrics strip */}
      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-3xl border border-sand bg-surface p-6 shadow-subtle hover:border-brass/40 transition-colors">
          <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-brass-deep">Audited Contracts</p>
          <p className="mt-3 font-display text-4xl text-charcoal">{files.length}</p>
        </div>
        <div className="rounded-3xl border border-sand bg-surface p-6 shadow-subtle hover:border-brass/40 transition-colors">
          <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-brass-deep">Verified & Indexed</p>
          <p className="mt-3 font-display text-4xl text-charcoal">
            {files.filter((f) => f.status.toUpperCase() === 'COMPLETED').length}
          </p>
        </div>
        <div className="rounded-3xl border border-sand bg-surface p-6 shadow-subtle hover:border-brass/40 transition-colors">
          <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-brass-deep">Awaiting Processing</p>
          <p className="mt-3 font-display text-4xl text-charcoal">
            {files.filter((f) => f.status.toUpperCase() !== 'COMPLETED').length}
          </p>
        </div>
        <div className="rounded-3xl border border-sand bg-surface p-6 shadow-subtle hover:border-brass/40 transition-colors">
           <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-brass-deep">Risk Flags</p>
           <p className="mt-3 font-display text-4xl text-charcoal">
             {files.filter((f) => f.status.toUpperCase() === 'FAILED' || f.status.toUpperCase() === 'NEEDS ATTENTION').length}
           </p>
        </div>
      </section>

      {/* Upload Drop Zone */}
      <section>
        <FileUpload onUploadSuccess={fetchFiles} />
      </section>

      {/* Document cards / table */}
      <section>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <Eyebrow>Contract Inventory</Eyebrow>
            <p className="text-sm text-stone-muted mt-1">
              Select an agreement to launch the dual-pane review workspace.
            </p>
          </div>
          <span className="text-xs font-mono text-muted rounded-full border border-sand bg-surface px-3 py-1 shadow-xs">
            {files.length} active
          </span>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 min-h-[300px]">
             <div className="space-y-4 w-full max-w-sm">
                <div className="flex items-center justify-between rounded-2xl border border-sand bg-parchment/60 p-4">
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="absolute inline-flex h-full w-full rounded-full bg-amber-deep opacity-75 motion-safe:animate-ping" />
                      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-deep" />
                    </span>
                    <span className="font-sans text-sm font-medium">Fetching repository state...</span>
                  </div>
                </div>
             </div>
          </div>
        ) : files.length === 0 ? (
          <div className="rounded-3xl border-2 border-dashed border-sand bg-parchment/40 py-24 text-center">
            <div className="mx-auto w-16 h-16 rounded-full border border-sand bg-surface shadow-card flex items-center justify-center mb-6">
               <File className="w-8 h-8 text-brass-deep" />
            </div>
            <h3 className="font-display text-2xl text-charcoal mb-2">
              Start your first review.
            </h3>
            <p className="text-sm text-stone-muted max-w-sm mx-auto mb-6">
              Upload a contract, NDA, or service agreement above to begin clause-level analysis.
            </p>
            <Button variant="pill-outline" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
               Upload a document ↑
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {files.map((file) => (
              <div
                key={file.id}
                className="group rounded-3xl border border-sand bg-surface p-6 shadow-subtle hover:shadow-card hover:border-brass/40 transition-all flex flex-col justify-between min-h-[220px]"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-5">
                    <div className="w-10 h-10 rounded-full bg-parchment border border-sand flex items-center justify-center text-brass-deep shadow-xs">
                      <FileText className="w-4 h-4" />
                    </div>
                    {getStatusBadge(file.status)}
                  </div>

                  <h3
                    className="font-display text-base font-bold text-charcoal mb-2 line-clamp-2"
                    title={file.file_name}
                  >
                    {file.file_name}
                  </h3>

                  <div className="flex items-center gap-2 text-[11px] font-mono text-muted mb-6">
                    <span className="rounded-full border border-sand bg-parchment px-2 py-0.5">PDF</span>
                    <span>•</span>
                    <span>{new Date(file.created_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-2 pt-4 border-t border-sand">
                  <div className="flex items-center gap-2">
                    <Button variant="pill-outline" size="sm" onClick={() => openPreview(file.id)}>
                      <ScanEye className="w-3.5 h-3.5 mr-1" />
                      Preview
                    </Button>
                    <Link to={`/document/${file.id}`}>
                      <Button variant="charcoal" size="sm">
                        <Eye className="w-3.5 h-3.5 mr-1" />
                        Workspace
                      </Button>
                    </Link>
                  </div>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-2 text-muted hover:text-crimson hover:bg-crimson-soft rounded-full transition-colors cursor-pointer border border-transparent hover:border-crimson/20"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
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
