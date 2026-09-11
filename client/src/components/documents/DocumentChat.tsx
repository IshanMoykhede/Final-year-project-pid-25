import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Bot, ChevronDown, ChevronUp, MessageSquare, Send, User } from 'lucide-react';
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

const ClauseList: React.FC<{ clauses: RetrievedClause[]; title: string }> = ({ clauses, title }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!clauses.length) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-gray-700"
        aria-expanded={isOpen}
      >
        <span>{title} ({clauses.length})</span>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {isOpen && (
        <div className="space-y-2 border-t border-gray-200 px-3 py-3">
          {clauses.map((clause) => (
            <div key={clause.chunk_id} className="rounded-md bg-white p-3 text-xs text-gray-600">
              <p className="mb-1 font-medium text-gray-800">
                {clause.aliases.length ? clause.aliases.join(', ') : `Clause ${clause.chunk_no}`}
              </p>
              <p className="whitespace-pre-wrap">{clause.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const DocumentChat: React.FC<DocumentChatProps> = ({ documentId }) => {
  const [question, setQuestion] = useState('');
  const [useExpansion, setUseExpansion] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

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
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown>{message.answer || 'No answer was generated.'}</ReactMarkdown>
                    </div>
                  </div>
                  <ClauseList clauses={message.primaryClauses} title="Primary clauses" />
                  <ClauseList clauses={message.expandedClauses} title="Related clauses" />
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
