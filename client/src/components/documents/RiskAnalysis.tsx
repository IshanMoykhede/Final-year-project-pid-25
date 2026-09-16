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
      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${riskStyles[clause.risk_level]}`}>{clause.risk_level}</span>
    </div>
    <p className="text-sm italic text-gray-600">“{clause.excerpt}”</p>
    <p className="text-sm text-gray-800">{clause.explanation_easy}</p>
    {clause.market_standard && <p className="text-xs text-gray-600"><strong>Market standard:</strong> {clause.market_standard}</p>}
    {clause.counter_offer && <p className="text-xs text-gray-600"><strong>Possible counter-offer:</strong> {clause.counter_offer}</p>}
  </article>
);

export const RiskAnalysis: React.FC<{ documentId: string }> = ({ documentId }) => {
  const [result, setResult] = useState<Awaited<ReturnType<typeof getDocumentRisk>> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadRisk = async (forceRefresh = false) => {
    setIsLoading(true);
    setError('');
    try {
      setResult(await getDocumentRisk(documentId, forceRefresh));
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { void loadRisk(); }, [documentId]);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-500" />Risk analysis</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => void loadRisk(true)} disabled={isLoading} title="Refresh risk analysis">
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && <div className="flex items-center gap-2 py-8 text-sm text-gray-500"><Loader2 className="h-5 w-5 animate-spin text-accent" />Reviewing clauses...</div>}
        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {result && !isLoading && (
          <>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-red-50 p-3"><strong className="block text-lg text-red-700">{result.high_risk_count}</strong>High risk</div>
              <div className="rounded-lg bg-amber-50 p-3"><strong className="block text-lg text-amber-700">{result.medium_risk_count}</strong>Needs attention</div>
              <div className="rounded-lg bg-emerald-50 p-3"><strong className="block text-lg text-emerald-700">{result.low_risk_count}</strong>Lower risk</div>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-gray-200 p-3 text-sm">
              {result.overall_risk === 'LOW' ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <AlertTriangle className="h-5 w-5 text-amber-600" />}
              Overall assessment: <strong>{result.overall_risk} risk</strong>
            </div>
            <div className="space-y-3">
              {result.clauses.map((clause) => <RiskItem key={clause.chunk_id} clause={clause} />)}
            </div>
            <p className="text-xs text-gray-500">This is an automated review for research and discussion, not legal advice.</p>
          </>
        )}
      </CardContent>
    </Card>
  );
};