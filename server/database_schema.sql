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

-- 5. Upcoming: clause_analysis Table (Phase 2 DeepClause)
-- Will cache the ReAct Agent's deep research and analysis to prevent redundant LLM calls.
CREATE TABLE clause_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    explanation_easy TEXT NOT NULL,
    faqs JSONB,
    risk_level TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH'
    counter_offer TEXT,
    market_standard TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
