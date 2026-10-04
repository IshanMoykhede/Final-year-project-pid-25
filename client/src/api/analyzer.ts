import { apiClient } from './client';

export interface ClauseCategoryCount {
  category: string;
  count: number;
}

export interface DocumentOverview {
  document_type: string;
  summary: string;
  parties: string[];
  jurisdiction: string;
  total_clauses: number;
  breakdown: ClauseCategoryCount[];
  recommended_roadmap: string[];
  recommended_starting_point: string;
  reasoning: string;
}

export interface ClauseAnalysisRequest {
  document_id: string;
  clause_type: string;
  original_text: string;
  document_overview: string;
  direct_references: string[];
  rag_results: string[];
  web_results: string[];
}

export interface ClauseAnalysisFaq {
  question: string;
  answer: string;
}

export interface ClauseAnalysis {
  explanation: string;
  entities_involved: string[];
  real_world_examples: string[];
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  risk_analysis: string;
  negotiation_advice: string;
  faqs: ClauseAnalysisFaq[];
  document_citations: string[];
  web_citations: string[];
  key_risks?: string[];
  revised_clause_text?: string;
}

export interface AnalysisSessionResponse {
  session_id?: string;
  document_id?: string;
  total_clauses: number;
  status: string;
}

export interface OrderedClauseItem {
  chunk_id: string;
  chunk_no: number;
  category?: string;
  aliases?: string[];
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
  risk_level?: string | null;
  has_analysis: boolean;
  preview_text: string;
}

export interface OrderedClauseListResponse {
  document_id: string;
  total_clauses: number;
  completed: number;
  in_progress: number;
  pending: number;
  clauses: OrderedClauseItem[];
}

export interface ClauseStepResponse {
  chunk_id: string;
  document_id: string;
  chunk_no: number;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING';
  cached: boolean;
  analysis: ClauseAnalysis;
}

export const getDocumentOverview = async (
  fileId: string,
  forceRefresh = false
): Promise<DocumentOverview> => {
  const response = await apiClient.get<DocumentOverview>(`/analyze/overview/${fileId}`, {
    params: { force_refresh: forceRefresh },
  });
  return response.data;
};

export const initializeAnalysisSession = async (fileId: string): Promise<AnalysisSessionResponse> => {
  const response = await apiClient.post<AnalysisSessionResponse>(`/analyze/session/initialize/${fileId}`);
  return response.data;
};

export const getOrderedClauses = async (fileId: string): Promise<OrderedClauseListResponse> => {
  const response = await apiClient.get<OrderedClauseListResponse>(`/analyze/clause/ordered-list/${fileId}`);
  return response.data;
};

export const analyzeClauseStep = async (chunkId: string, forceRefresh = false): Promise<ClauseStepResponse> => {
  const response = await apiClient.post<ClauseStepResponse>(`/analyze/clause/step/${encodeURIComponent(chunkId)}`, null, {
    params: { force_refresh: forceRefresh },
  });
  return response.data;
};

export const analyzeClause = async (
  chunkId: string,
  request: ClauseAnalysisRequest
): Promise<ClauseAnalysis> => {
  const response = await apiClient.post<ClauseAnalysis>(
    `/analyze/clause/${encodeURIComponent(chunkId)}`,
    request
  );
  return response.data;
};