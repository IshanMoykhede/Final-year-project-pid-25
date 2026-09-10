import { apiClient } from './client';

export interface FileData {
  id: string;
  user_id: string;
  file_name: string;
  storage_path: string;
  content_type: string;
  status: string;
  raw_markdown?: string;
  created_at?: string;
}

export interface GenericResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export const uploadFile = async (file: File): Promise<GenericResponse<{ file_id: string; file_name: string }>> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/file-upload/upload-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getMyFiles = async (): Promise<GenericResponse<FileData[]>> => {
  const response = await apiClient.get('/file-upload/my-files');
  return response.data;
};

export interface FilePreviewData {
  signedURL?: string;
  signedUrl?: string;
  url?: string;
  publicURL?: string;
  publicUrl?: string;
}

export const getFilePreview = async (fileId: string): Promise<GenericResponse<string | FilePreviewData>> => {
  const response = await apiClient.get(`/file-upload/preview/${fileId}`);
  return response.data;
};

export const viewFile = async (fileId: string) => {
  const response = await apiClient.get(`/file-upload/view/${fileId}`, {
    responseType: 'blob',
    headers: {
      Accept: 'application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/octet-stream',
    },
  });

  return response;
};

export const deleteFile = async (fileId: string): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete(`/file-upload/${fileId}`);
  return response.data;
};

export interface OcrResponse {
  markdown: string;
  text: string;
  raw_llama_json: any[];
}

export const processDocument = async (fileId: string): Promise<GenericResponse<OcrResponse>> => {
  const response = await apiClient.get(`/file-upload/test-ocr/${fileId}`);
  return response.data;
};

export const testOcrRoute = processDocument;
