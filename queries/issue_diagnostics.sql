-- Find all failed login attempts
SELECT * FROM logins WHERE status = 'failed';

-- Check open issues by module
SELECT module, COUNT(*) FROM issues WHERE status='open' GROUP BY module;

-- Resolve a specific issue
UPDATE issues SET status='resolved' WHERE id=102;