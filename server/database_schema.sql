-- Enable Vector Support (Required for pgvector semantic search)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. The files Table
-- Tracks the uploaded document, its state machine status, and caches the Document Overview.
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- References auth.users (if using Supabase Auth)
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL, -- Supabase Storage URL
    status TEXT NOT NULL DEFAULT 'UPLOADED', -- 'OCR_COMPLETED', 'COMPLETED', etc.
    overview_cache JSONB, -- Added for Phase 1 of DeepClause Analyzer
    risk_cache JSONB, -- Added for Phase 2 of DeepClause Analyzer (Document Risk Analysis)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. The classifications Table
-- Lookup table for the categories used to classify chunks (e.g., "Financial", "Termination").
CREATE TABLE classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. The chunks Table
-- The core of Agentic RAG. Holds segmented text, classification, aliases, and 384D vectors.
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    classification_id UUID REFERENCES classifications(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    aliases JSONB, -- E.g., ["Article 4", "Section 4.1", "Base Rent"]
    bbox JSONB, -- OCR coordinates with page_number for citation highlighting
    embedding VECTOR(384), -- Generated via HuggingFace Sentence-Transformers (all-MiniLM-L6-v2)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 4. The cross_references Table (Layer 2 Linking)
-- Powers the deterministic direct-reference engine, bridging two chunks together.
CREATE TABLE cross_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    target_chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    reference_text TEXT NOT NULL, -- The raw text that caused the link (e.g., "Article 11")
    match_type TEXT NOT NULL, -- 'EXACT_MATCH' or 'UNRESOLVED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 5. Analysis Sessions Table (Progress Tracker)
-- One row per document analysis run. The frontend polls this single row
-- to show a progress bar instead of counting clause_analysis rows every time.
CREATE TABLE analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,

    -- Counters (updated atomically as each clause finishes)
    total_clauses INT NOT NULL DEFAULT 0,
    completed INT NOT NULL DEFAULT 0,
    failed INT NOT NULL DEFAULT 0,
    in_progress INT NOT NULL DEFAULT 0,

    -- Overall session state machine
    status TEXT NOT NULL DEFAULT 'INITIALIZED',
    -- Values: 'INITIALIZED' | 'RUNNING' | 'COMPLETED' | 'PAUSED' | 'FAILED'

    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Unique constraint: one active session per document
    CONSTRAINT uq_session_per_document UNIQUE (document_id)
);

-- 6. Clause Analysis Table (Per-Clause Results + Status)
-- One row per chunk. Stores the full agent output and tracks per-clause status.
-- Maps 1:1 to ClauseAnalysisOutput from the LangGraph Agent.
CREATE TABLE clause_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE SET NULL,

    -- Per-clause status tracking
    status TEXT NOT NULL DEFAULT 'PENDING',
    -- Values: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'

    -- ===== Agent Output Fields (match ClauseAnalysisOutput exactly) =====
    explanation TEXT,                     -- Plain English explanation for non-lawyers
    entities_involved JSONB,              -- ["Landlord", "Tenant"]
    real_world_examples JSONB,            -- ["Hypothetical example: ..."]
    risk_level TEXT,                      -- 'LOW' | 'MEDIUM' | 'HIGH' (denormalized for fast filtering)
    risk_analysis TEXT,                   -- Why this risk level was assigned
    negotiation_advice TEXT,              -- Counter-offers / negotiation tips
    faqs JSONB,                           -- [{"question": "...", "answer": "..."}]
    document_citations JSONB,             -- ["chunk-uuid-1", "chunk-uuid-2"]
    web_citations JSONB,                  -- ["https://example.com/..."]

    -- ===== Error Tracking =====
    error_message TEXT,                   -- If status = 'FAILED', stores the error reason
    retry_count INT NOT NULL DEFAULT 0,   -- How many times we retried this clause

    -- ===== Timestamps =====
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),

    -- One analysis per chunk (prevents duplicates, enables upsert)
    CONSTRAINT uq_analysis_per_chunk UNIQUE (chunk_id)
);

-- Fast index for progress queries: "give me all clause statuses for this document"
CREATE INDEX idx_clause_analysis_doc_status ON clause_analysis(document_id, status);

-- Fast index for risk filtering: "show me all HIGH risk clauses in this document"
CREATE INDEX idx_clause_analysis_doc_risk ON clause_analysis(document_id, risk_level);

-- 7. Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    retrieved_chunk_ids UUID[] DEFAULT '{}',
    is_expanded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast retrieval of document conversation threads
CREATE INDEX IF NOT EXISTS idx_chat_messages_doc_created ON chat_messages(document_id, created_at);

-- Add risk_cache column to files if not exists
ALTER TABLE files ADD COLUMN IF NOT EXISTS risk_cache JSONB;

-- Storage policies for Files bucket
CREATE POLICY "Allow public uploads to Files bucket"
ON storage.objects
FOR INSERT
TO public
WITH CHECK (bucket_id = 'Files');

CREATE POLICY "Allow public reads from Files bucket"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'Files');
