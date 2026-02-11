-- Base tables: sessions, telemetry_records, device_heartbeats
-- Run this before 001_device_events.sql

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255),
    device_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_metadata JSONB
);

CREATE INDEX IF NOT EXISTS ix_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS ix_sessions_device_id ON sessions(device_id);

CREATE TABLE IF NOT EXISTS telemetry_records (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    seq INTEGER NOT NULL,
    type VARCHAR(100) NOT NULL,
    device_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB
);

CREATE INDEX IF NOT EXISTS ix_telemetry_records_session_id ON telemetry_records(session_id);

CREATE TABLE IF NOT EXISTS device_heartbeats (
    id SERIAL PRIMARY KEY,
    device_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    battery_pct INTEGER,
    network JSONB,
    storage_free_mb INTEGER,
    camera JSONB
);
