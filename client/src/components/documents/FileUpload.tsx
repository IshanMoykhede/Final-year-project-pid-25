import React, { useState } from 'react';
import { uploadFile } from '../../api/files';
import { Button } from '../common/Button';
import { UploadCloud, File as FileIcon, X, CheckCircle2 } from 'lucide-react';
import { cn } from '../common/Button';
import { Eyebrow } from '../common/Eyebrow';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    setError('');
    setIsSuccess(false);
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(file.type) && !['pdf', 'docx', 'txt'].includes(extension || '')) {
      setError('Only PDF, DOCX, and TXT files are allowed.');
      return;
    }
    
    if (file.size > 200 * 1024 * 1024) {
      setError('File size must be under 200MB.');
      return;
    }
    
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError('');
    try {
      await uploadFile(selectedFile);
      setIsSuccess(true);
      setTimeout(() => {
        setSelectedFile(null);
        setIsSuccess(false);
        onUploadSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to upload file');
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      <Eyebrow>Ingest Agreement</Eyebrow>
      
      {!selectedFile ? (
        <div className="flex flex-col items-center">
          <div
            className={cn(
              'relative flex flex-col items-center justify-center w-full p-8 border-2 border-dashed rounded-3xl transition-all',
              dragActive ? 'border-brass bg-brass-subtle/20' : 'border-sand bg-parchment/40 hover:border-brass/50 hover:bg-parchment/60'
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleChange}
              accept=".pdf,.docx,.txt"
            />
            
            <div className="w-14 h-14 mb-5 flex items-center justify-center rounded-full border border-sand bg-surface shadow-card">
               <UploadCloud className="w-6 h-6 text-brass-deep" />
            </div>
            
            <p className="font-display text-lg text-charcoal mb-1">Drop your agreement here.</p>
            <p className="font-clause text-sm text-stone-muted">or click to select — PDF, DOCX, TXT up to 200MB</p>
          </div>
          
          <div className="flex gap-2 mt-4">
             {['PDF', 'DOCX', 'TXT'].map((ext) => (
               <span key={ext} className="rounded-full border border-sand bg-surface px-3 py-1 font-mono text-[10px] text-muted shadow-xs">
                 {ext}
               </span>
             ))}
          </div>
        </div>
      ) : (
        <div 
          className={cn(
            "flex flex-col items-center justify-center w-full p-8 border rounded-3xl transition-colors relative",
            isSuccess ? "border-olive/40 bg-olive-soft/30" : "border-sand bg-surface shadow-subtle"
          )}
        >
          {!isUploading && !isSuccess && (
            <button
              onClick={() => setSelectedFile(null)}
              className="absolute top-4 right-4 p-2 rounded-full text-muted hover:bg-parchment transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          
          {isSuccess ? (
             <>
               <CheckCircle2 className="w-12 h-12 text-olive mb-3" />
               <p className="text-sm font-medium text-olive">Ingested — ready for indexing.</p>
             </>
          ) : (
             <>
                <div className="w-14 h-14 mb-4 flex items-center justify-center rounded-full border border-sand bg-parchment">
                   <FileIcon className="w-6 h-6 text-brass-deep" />
                </div>
                <p className="font-display text-base font-bold text-charcoal truncate max-w-[250px] sm:max-w-xs mb-1">
                  {selectedFile.name}
                </p>
                <p className="font-mono text-[11px] text-muted mb-6">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
                
                {isUploading ? (
                  <div className="w-full max-w-xs">
                    <div className="h-1.5 w-full bg-sand/50 rounded-full overflow-hidden mb-2 relative">
                       <div className="h-full bg-brass w-1/2 animate-pulse absolute left-0 top-0"></div>
                    </div>
                    <div className="flex items-center justify-center gap-2 font-mono text-xs text-brass-deep">
                       <span className="relative flex h-2 w-2">
                         <span className="absolute inline-flex h-full w-full rounded-full bg-brass opacity-75 motion-safe:animate-ping" />
                         <span className="relative inline-flex h-2 w-2 rounded-full bg-brass" />
                       </span>
                       Uploading contract...
                    </div>
                  </div>
                ) : (
                  <Button onClick={handleUpload} variant="charcoal" className="w-full max-w-xs">
                    Upload Document
                  </Button>
                )}
             </>
          )}
        </div>
      )}
      {error && (
        <div className="mt-3 rounded-2xl border border-crimson/30 bg-crimson-soft p-3 text-center font-mono text-xs text-crimson">
          {error}
        </div>
      )}
    </div>
  );
};
