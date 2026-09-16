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

export const getDocumentOverview = async (
  fileId: string,
  forceRefresh = false
): Promise<DocumentOverview> => {
  const response = await apiClient.get<DocumentOverview>(`/analyze/overview/${fileId}`, {
    params: { force_refresh: forceRefresh },
  });
  return response.data;
};