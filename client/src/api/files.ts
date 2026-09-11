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
  const response = await apiClient.get<GenericResponse<{ signedUrl?: string; signedURL?: string; url?: string } | string>>(
    `/file-upload/preview/${fileId}`
  );

  const previewData = response.data?.data;
  let signedUrl = '';

  if (typeof previewData === 'string') {
    signedUrl = previewData;
  } else if (previewData && typeof previewData === 'object') {
    signedUrl = previewData.signedUrl || previewData.signedURL || previewData.url || '';
  }

  // Fetch the actual file blob using the temporary signed URL
  if (signedUrl) {
    const fileResponse = await fetch(signedUrl);
    const blob = await fileResponse.blob();
    return {
      data: blob,
      headers: {
        'content-type': fileResponse.headers.get('content-type') || 'application/pdf',
      },
    };
  }

  throw new Error('Signed URL could not be generated for preview.');
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

export interface PreprocessEvent {
  step: string;
  status: string;
  message: string;
}

export const preprocessDocument = async (
  fileId: string,
  onEvent?: (event: PreprocessEvent) => void
): Promise<PreprocessEvent[]> => {
  const baseUrl = apiClient.defaults.baseURL || '';
  const response = await fetch(`${baseUrl}/file-upload/preprocess/${fileId}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Document preprocessing failed (${response.status}).`);
  }

  if (!response.body) {
    throw new Error('Document preprocessing did not return a progress stream.');
  }

  const events: PreprocessEvent[] = [];
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const consumeBuffer = (flush = false) => {
    const lines = buffer.split('\n');
    buffer = flush ? '' : lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data:')) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;

      const event = JSON.parse(payload) as PreprocessEvent;
      events.push(event);
      onEvent?.(event);
      if (event.status === 'error') {
        throw new Error(event.message || `Document preprocessing failed during ${event.step.toLowerCase()}.`);
      }
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    consumeBuffer(done);
    if (done) break;
  }

  return events;
};
