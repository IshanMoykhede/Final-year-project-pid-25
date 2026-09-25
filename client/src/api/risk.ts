/* =========================================================================
 * Risk Feature Temporarily Disabled
 * =========================================================================
import { apiClient } from './client';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface ClauseRisk {
  chunk_id: string;
  category: string;
  excerpt: string;
  risk_level: RiskLevel;
  risk_score?: number;
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

export interface RawRiskItemBackend {
  chunk_id: string;
  chunk_text: string;
  risk_level: RiskLevel;
  risk_score?: number;
  clause_title: string;
  explanation: string;
  compliance_check?: string;
  recommendation?: string;
}

export interface BackendRiskResponse {
  high_risks?: RawRiskItemBackend[];
  medium_risks?: RawRiskItemBackend[];
  low_risks?: RawRiskItemBackend[];
  total_risks?: number;
  overall_risk?: RiskLevel;
  high_risk_count?: number;
  medium_risk_count?: number;
  low_risk_count?: number;
  clauses?: ClauseRisk[];
}

export const getDocumentRisk = async (fileId: string, forceRefresh = false): Promise<RiskAnalysis> => {
  // Disabled
  return {
    overall_risk: 'LOW',
    high_risk_count: 0,
    medium_risk_count: 0,
    low_risk_count: 0,
    clauses: [],
  };
};
========================================================================= */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface ClauseRisk {
  chunk_id: string;
  category: string;
  excerpt: string;
  risk_level: RiskLevel;
  risk_score?: number;
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

export const getDocumentRisk = async (_fileId: string, _forceRefresh = false): Promise<RiskAnalysis> => {
  return {
    overall_risk: 'LOW',
    high_risk_count: 0,
    medium_risk_count: 0,
    low_risk_count: 0,
    clauses: [],
  };
};