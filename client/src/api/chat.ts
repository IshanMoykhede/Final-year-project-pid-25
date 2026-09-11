import { apiClient } from './client';

export interface RetrievedClause {
  chunk_id: string;
  chunk_no: number;
  text: string;
  aliases: string[];
  similarity?: number | null;
  is_expanded: boolean;
}

export interface ChatRequest {
  document_id: string;
  question: string;
  use_1hop_expansion: boolean;
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
