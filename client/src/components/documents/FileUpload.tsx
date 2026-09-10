import React, { useState } from 'react';
import { uploadFile } from '../../api/files';
import { Button } from '../common/Button';
import { UploadCloud, File, X } from 'lucide-react';
import { cn } from '../common/Button';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
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
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      setError('Only PDF and DOCX files are allowed.');
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
      setSelectedFile(null);
      onUploadSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          className={cn(
            'relative flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl transition-colors bg-gray-50',
            dragActive ? 'border-accent bg-accent/5' : 'border-gray-300 hover:border-accent hover:bg-accent/5'
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
            accept=".pdf,.docx"
          />
          <UploadCloud className="w-10 h-10 text-gray-400 mb-3" />
          <p className="text-sm font-medium text-gray-700">Click or drag file to this area to upload</p>
          <p className="text-xs text-gray-500 mt-1">Support for a single PDF or DOCX file.</p>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center w-full h-48 border rounded-xl bg-white shadow-sm p-6 relative">
          <button
            onClick={() => setSelectedFile(null)}
            disabled={isUploading}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
          <File className="w-12 h-12 text-accent mb-3" />
          <p className="text-sm font-medium text-gray-900 truncate max-w-xs">{selectedFile.name}</p>
          <p className="text-xs text-gray-500 mt-1 mb-4">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
          <Button onClick={handleUpload} isLoading={isUploading} className="w-full max-w-xs">
            Upload Document
          </Button>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
    </div>
  );
};
