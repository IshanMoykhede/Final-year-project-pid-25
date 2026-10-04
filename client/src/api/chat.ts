import { apiClient } from './client';

export interface RetrievedClause {
  chunk_id: string;
  chunk_no: number;
  text: string;
  aliases: string[];
  similarity?: number | null;
  is_expanded?: boolean;
  bbox: Array<Record<string, unknown>>;
  page_no?: number | null;
}

export interface ChatRequest {
  document_id: string;
  question: string;
  use_1hop_expansion: boolean;
  save_history?: boolean;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  primary_clauses: RetrievedClause[];
  expanded_clauses: RetrievedClause[];
}

export const askDocumentQuestion = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/chat/ask', request);
  return response.data;
};

export interface ChatMessageData {
  id: string;
  document_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  retrieved_chunk_ids: string[];
  is_expanded: boolean;
  created_at: string;
  clauses?: RetrievedClause[];
}

export const getChatHistory = async (documentId: string): Promise<ChatMessageData[]> => {
  const response = await apiClient.get<{ messages: ChatMessageData[] }>(`/chat/${documentId}/history`);
  return response.data.messages;
};
