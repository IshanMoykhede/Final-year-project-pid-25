import { apiClient } from './client';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface ClauseRisk {
  chunk_id: string;
  category: string;
  excerpt: string;
  risk_level: RiskLevel;
  explanation_easy: string;
  counter_offer?: string | null;
  market_standard?: string | null;
}

export interface RiskAnalysis {
  overall_risk: RiskLevel;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  clauses: ClauseRisk[];
}

export const getDocumentRisk = async (fileId: string, forceRefresh = false): Promise<RiskAnalysis> => {
  const response = await apiClient.get<RiskAnalysis>(`/analyze/risk/${fileId}`, {
    params: { force_refresh: forceRefresh },
  });
  return response.data;
};