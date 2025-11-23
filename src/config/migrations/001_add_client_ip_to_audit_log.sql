-- Migration: Add client_ip column to audit_log table
-- Date: 2025-11-23
-- Description: Track the IP address of clients making API requests for security auditing

ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS client_ip VARCHAR(45);

-- Add index for client_ip lookups
CREATE INDEX IF NOT EXISTS idx_audit_log_client_ip ON audit_log(client_ip);

-- Add comment
COMMENT ON COLUMN audit_log.client_ip IS 'IP address of the client that made the API request';
