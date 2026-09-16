import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyFiles, deleteFile } from '../api/files';
import type { FileData } from '../api/files';
import { FileUpload } from '../components/documents/FileUpload';
import { Button } from '../components/common/Button';
import { Card, CardContent } from '../components/common/Card';
import { FileText, Trash2, Eye, File, Loader2, ScanEye, Upload, Sparkles } from 'lucide-react';

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
    if (!window.confirm('Are you sure you want to delete this file?')) return;
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

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-5 border-b border-gray-200 pb-8 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="mb-2 text-sm font-semibold uppercase tracking-widest text-accent">Workspace</p><h1 className="text-3xl font-bold text-gray-950">Your document desk</h1><p className="mt-2 text-gray-500">Upload, organize, and review your legal documents in one place.</p></div>
        <div className="flex items-center gap-2 text-sm text-gray-500"><Sparkles className="h-4 w-4 text-accent" />AI-assisted review</div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5"><p className="text-sm text-gray-500">Total documents</p><p className="mt-2 text-3xl font-semibold text-gray-950">{files.length}</p></div>
        <div className="rounded-xl border border-gray-200 bg-white p-5"><p className="text-sm text-gray-500">Ready to review</p><p className="mt-2 text-3xl font-semibold text-gray-950">{files.filter((file) => file.status.toUpperCase() === 'COMPLETED').length}</p></div>
        <div className="rounded-xl border border-gray-200 bg-sky-50 p-5"><p className="text-sm text-sky-700">Next step</p><p className="mt-2 text-sm font-semibold text-sky-950">Upload a document to begin</p></div>
      </div>

      <section>
        <div className="mb-4 flex items-center gap-2"><Upload className="h-5 w-5 text-accent" /><h2 className="text-lg font-semibold text-gray-900">Upload new document</h2></div>
        <FileUpload onUploadSuccess={fetchFiles} />
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between"><div><h2 className="text-lg font-semibold text-gray-900">Your documents</h2><p className="mt-1 text-sm text-gray-500">Open a file to preview, chat, or review risk.</p></div><span className="text-sm text-gray-500">{files.length} total</span></div>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50">
            <File className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No documents uploaded yet</p>
            <p className="text-sm text-gray-400 mt-1">Upload a document above to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {files.map((file) => (
              <Card key={file.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-5 flex flex-col h-full">
                  <div className="flex items-start justify-between mb-4">
                    <div className="bg-accent/10 p-2.5 rounded-lg text-accent">
                      <FileText className="w-6 h-6" />
                    </div>
                    <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 capitalize">
                      {file.status}
                    </span>
                  </div>
                  <h3 className="font-medium text-gray-900 mb-1 truncate" title={file.file_name}>
                    {file.file_name}
                  </h3>
                  <p className="text-xs text-gray-500 mb-6 mt-auto">
                    {new Date(file.created_at || Date.now()).toLocaleDateString()}
                  </p>
                  
                  <div className="flex items-center justify-between gap-2 mt-auto pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => openPreview(file.id)}>
                        <ScanEye className="w-4 h-4 mr-2" />
                        Preview
                      </Button>
                      <Link to={`/document/${file.id}`}>
                        <Button size="sm">
                          <Eye className="w-4 h-4 mr-2" />
                          Analyze
                        </Button>
                      </Link>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(file.id)} className="text-red-500 hover:text-red-600 hover:bg-red-50">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
