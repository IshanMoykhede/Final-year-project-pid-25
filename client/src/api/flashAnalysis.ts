import { apiClient } from './client';

export interface FlashAnalysisWarning {
  title: string;
  detail: string;
}

export interface FlashAnalysisCategory {
  category: string;
  key_clauses: string;
  favorable_terms: string;
  risks: string;
  obligations: string;
  clause_references: string;
}

export interface FlashAnalysisReport {
  overall_verdict: string;
  document_overview: string;
  category_analysis: FlashAnalysisCategory[];
  important_warnings: FlashAnalysisWarning[];
  before_you_sign: string[];
}

export interface FlashAnalysisResponse {
  success: boolean;
  document_id: string;
  file_name: string;
  chunk_count: number;
  report: FlashAnalysisReport;
}

export const generateFlashAnalysis = async (documentId: string): Promise<FlashAnalysisResponse> => {
  const response = await apiClient.post<FlashAnalysisResponse>(
    `/api/flash-analysis/${encodeURIComponent(documentId)}`
  );
  return response.data;
};
