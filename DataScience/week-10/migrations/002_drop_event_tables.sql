-- Remove event config and messages; oil-change is derived from device_odometer (total_km >= 2000) in API.

DROP TABLE IF EXISTS device_messages;
DROP TABLE IF EXISTS device_event_config;
