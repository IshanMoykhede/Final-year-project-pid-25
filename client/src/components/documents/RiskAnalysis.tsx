import React from 'react';

// Risk Analysis feature disabled
export const RiskAnalysis: React.FC<{ documentId: string }> = () => {
  return null;
};

/*
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, CheckCircle2, Loader2, RefreshCw } from 'lucide-react';
import { getDocumentRisk } from '../../api/risk';
import type { ClauseRisk, RiskLevel } from '../../api/risk';
import { Button } from '../common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';

const riskStyles: Record<RiskLevel, string> = {
  HIGH: 'bg-red-100 text-red-700',
  MEDIUM: 'bg-amber-100 text-amber-700',
  LOW: 'bg-emerald-100 text-emerald-700',
};

const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string') return error.response.data.detail;
  return error instanceof Error ? error.message : 'Unable to generate risk analysis.';
};

const RiskItem: React.FC<{ clause: ClauseRisk }> = ({ clause }) => (
  <article className="space-y-3 rounded-lg border border-gray-200 p-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <span className="text-xs font-medium uppercase tracking-wide text-gray-500">{clause.category}</span>
      <div className="flex items-center gap-1.5">
        {clause.risk_score !== undefined && (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 border border-gray-200">
            Score: {clause.risk_score}/100
          </span>
        )}
        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${riskStyles[clause.risk_level]}`}>{clause.risk_level}</span>
      </div>
    </div>
    <p className="text-sm italic text-gray-600">“{clause.excerpt}”</p>
    <p className="text-sm text-gray-800">{clause.explanation_easy}</p>
    {clause.market_standard && <p className="text-xs text-gray-600"><strong>Market standard:</strong> {clause.market_standard}</p>}
    {clause.counter_offer && <p className="text-xs text-gray-600"><strong>Possible counter-offer:</strong> {clause.counter_offer}</p>}
  </article>
);
*/