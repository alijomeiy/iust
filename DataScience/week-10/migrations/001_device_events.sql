-- Migration: New tables and columns for distance calculation and device events

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS device_id VARCHAR(255);

CREATE TABLE IF NOT EXISTS device_event_config (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    km_threshold FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS device_odometer (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    total_km FLOAT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device_messages (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    event_config_id INT NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    message JSONB,
    km_at_trigger FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Example: device M001 maintenance due at 20000 km
-- INSERT INTO device_event_config (device_id, event_name, km_threshold)
-- VALUES ('M001', 'maintenance_due', 20000);
