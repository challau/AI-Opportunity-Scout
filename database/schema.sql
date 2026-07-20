-- AI Opportunity Scout — Database Schema
-- Compatible with PostgreSQL 16 + pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search

-- ─── Users ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password TEXT,
    avatar_url TEXT,
    google_id VARCHAR(255) UNIQUE,
    github_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ─── Profiles ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    country VARCHAR(100),
    college VARCHAR(255),
    student_year INTEGER,
    interested_domains TEXT[] DEFAULT '{}',
    programming_languages TEXT[] DEFAULT '{}',
    preferred_platforms TEXT[] DEFAULT '{}',
    email_notifications BOOLEAN DEFAULT TRUE,
    telegram_notifications BOOLEAN DEFAULT FALSE,
    notification_frequency VARCHAR(20) DEFAULT 'daily',
    telegram_chat_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Events ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    short_summary TEXT,
    platform VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    domains TEXT[] DEFAULT '{}',
    programming_languages TEXT[] DEFAULT '{}',
    prize VARCHAR(500),
    prize_amount FLOAT,
    location VARCHAR(255),
    is_remote BOOLEAN DEFAULT FALSE,
    is_free BOOLEAN DEFAULT TRUE,
    eligibility TEXT,
    organizer VARCHAR(255),
    registration_deadline TIMESTAMPTZ,
    event_start_date TIMESTAMPTZ,
    event_end_date TIMESTAMPTZ,
    registration_url TEXT NOT NULL,
    image_url TEXT,
    source_url TEXT,
    ai_score FLOAT DEFAULT 0.0,
    popularity_score FLOAT DEFAULT 0.0,
    embedding vector(1536),
    content_hash VARCHAR(64),
    external_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    participant_count INTEGER DEFAULT 0,
    extra_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    crawled_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_platform ON events(platform);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_deadline ON events(registration_deadline);
CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active);
CREATE INDEX IF NOT EXISTS idx_events_hash ON events(content_hash);
CREATE INDEX IF NOT EXISTS idx_events_score ON events(ai_score DESC);
CREATE INDEX IF NOT EXISTS idx_events_title_gin ON events USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_events_embedding ON events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─── Saved Events ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_events(user_id);

-- ─── Notifications ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    body TEXT,
    type VARCHAR(50) DEFAULT 'info',
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    channel VARCHAR(20) DEFAULT 'in_app',
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(user_id, is_read);

-- ─── Resumes ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    extracted_text TEXT,
    skills JSONB DEFAULT '{}',
    embedding vector(1536),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);

-- ─── Crawler Logs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crawler_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    events_found INTEGER DEFAULT 0,
    events_new INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_crawler_platform ON crawler_logs(platform);

-- ─── Scheduler Logs ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scheduler_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    duration_seconds FLOAT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
