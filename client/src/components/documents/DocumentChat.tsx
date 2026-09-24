import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, ChevronDown, ChevronUp, LocateFixed, MessageSquare, Send, User } from 'lucide-react';
import { askDocumentQuestion } from '../../api/chat';
import type { RetrievedClause } from '../../api/chat';
import { Button } from '../common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';

interface ChatMessage {
  id: number;
  question: string;
  answer: string;
  primaryClauses: RetrievedClause[];
  expandedClauses: RetrievedClause[];
}

interface DocumentChatProps {
  documentId: string;
  onCitation?: (clause: RetrievedClause) => void;
}

const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
      return detail.message;
    }
  }

  if (error instanceof Error) return error.message;
  return 'Unable to get an answer right now. Please try again.';
};

const ClauseList: React.FC<{
  clauses: RetrievedClause[];
  title: string;
  onCitation?: (clause: RetrievedClause) => void;
}> = ({ clauses, title, onCitation }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!clauses.length) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-sand bg-[#FAF7F0]/60 shadow-xs transition-colors">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="flex w-full items-center justify-between px-3.5 py-2.5 text-left text-xs font-medium text-[#57534E] hover:bg-[#F4EDE6]/60 transition-colors"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-[#B08D57]" />
          <span>{title}</span>
          <span className="rounded-full bg-sand/60 px-1.5 py-0.2 font-mono text-[10px] text-muted">
            {clauses.length}
          </span>
        </span>
        {isOpen ? <ChevronUp className="h-3.5 w-3.5 text-muted" /> : <ChevronDown className="h-3.5 w-3.5 text-muted" />}
      </button>

      {isOpen && (
        <div className="space-y-3 border-t border-sand/70 p-3 bg-white">
          {clauses.map((clause) => (
            <div
              key={clause.chunk_id}
              className="rounded-lg border border-sand/80 bg-[#FAF7F0]/30 p-3.5 text-xs text-charcoal shadow-2xs hover:border-[#B08D57]/40 transition-colors"
            >
              <div className="mb-2 flex items-center justify-between gap-2 border-b border-sand/50 pb-2">
                <span className="font-serif font-semibold tracking-tight text-charcoal">
                  {clause.aliases.length ? clause.aliases.join(', ') : `Clause ${clause.chunk_no}`}
                </span>

                {onCitation && (
                  <button
                    type="button"
                    onClick={() => onCitation(clause)}
                    disabled={!clause.bbox.length}
                    title={clause.bbox.length ? 'Locate and highlight this citation in document preview' : 'No coordinates available'}
                    className="inline-flex items-center gap-1 rounded-md border border-[#B08D57]/40 bg-surface px-2.5 py-1 font-mono text-[11px] font-medium text-brass-deep transition hover:bg-brass-subtle hover:border-brass disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <LocateFixed className="h-3 w-3 text-brass" />
                    Cite
                  </button>
                )}
              </div>

              {/* Rendered content with full Markdown table and typography support */}
              <div className="prose prose-xs max-w-none text-charcoal prose-p:my-1 prose-headings:text-xs prose-headings:font-bold prose-headings:text-charcoal prose-table:my-2 prose-th:bg-parchment prose-th:p-2 prose-th:text-left prose-th:font-semibold prose-th:text-xs prose-td:p-2 prose-td:border-t prose-td:border-sand prose-td:text-xs overflow-x-auto">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {clause.text}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const DocumentChat: React.FC<DocumentChatProps> = ({ documentId, onCitation }) => {
  const [question, setQuestion] = useState('');
  const [useExpansion, setUseExpansion] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (typeof window === 'undefined') return [];

    try {
      const savedMessages = window.localStorage.getItem(`document-chat:${documentId}`);
      const parsedMessages: unknown = savedMessages ? JSON.parse(savedMessages) : [];
      return Array.isArray(parsedMessages) ? (parsedMessages as ChatMessage[]) : [];
    } catch {
      return [];
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    try {
      window.localStorage.setItem(`document-chat:${documentId}`, JSON.stringify(messages));
    } catch {
    }
  }, [documentId, messages]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isLoading) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await askDocumentQuestion({
        document_id: documentId,
        question: trimmedQuestion,
        use_1hop_expansion: useExpansion,
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: Date.now(),
          question: trimmedQuestion,
          answer: response.answer,
          primaryClauses: response.primary_clauses,
          expandedClauses: response.expanded_clauses,
        },
      ]);
      setQuestion('');
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-accent" />
          Ask about this document
        </CardTitle>
        <p className="text-sm text-gray-500">
          Ask a question and get an answer grounded in the clauses from this document.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {messages.length > 0 && (
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="space-y-3">
                <div className="flex gap-2 rounded-lg bg-gray-100 p-3 text-sm text-gray-800">
                  <User className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
                  <p>{message.question}</p>
                </div>
                <div className="space-y-3 rounded-lg border border-accent/20 bg-accent/5 p-3 text-sm text-gray-700">
                  <div className="flex gap-2">
                    <Bot className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                    <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-gray-900 prose-headings:my-2 prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 text-gray-800 leading-relaxed overflow-x-auto">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.answer || 'No answer was generated.'}
                      </ReactMarkdown>
                    </div>
                  </div>
                  <ClauseList clauses={message.primaryClauses} title="Primary clauses" onCitation={onCitation} />
                  <ClauseList clauses={message.expandedClauses} title="Related clauses" onCitation={onCitation} />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="e.g. What are the termination requirements?"
            rows={3}
            maxLength={2000}
            disabled={isLoading}
            className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20 disabled:bg-gray-50"
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-2 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={useExpansion}
                onChange={(event) => setUseExpansion(event.target.checked)}
                disabled={isLoading}
                className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
              />
              Include related clauses
            </label>
            <Button type="submit" size="sm" isLoading={isLoading} disabled={!question.trim()}>
              <Send className="mr-2 h-4 w-4" />
              Ask question
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
