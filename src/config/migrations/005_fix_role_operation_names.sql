-- Migration 005: Fix role operation names to include API prefix
--
-- Root cause: Operations stored in role_operations used unprefixed names
-- (e.g., "createVlan") but MCP tool names use "{api_name}_{operation_id}"
-- format (e.g., "manage_createVlan"). This caused role-based filtering to
-- never match, making manually-created roles ineffective.

-- Update existing role_operations that have unprefixed names by looking up
-- the api_name from the api_endpoints table
UPDATE role_operations ro
SET operation_name = ep.api_name || '_' || ro.operation_name
FROM api_endpoints ep
WHERE ro.operation_name = ep.operation_id
  AND ro.operation_name NOT LIKE '%\_%';

-- Handle potential duplicates after prefix update (if somehow both prefixed
-- and unprefixed versions exist)
DELETE FROM role_operations
WHERE id NOT IN (
    SELECT MIN(id)
    FROM role_operations
    GROUP BY role_id, operation_name
);
