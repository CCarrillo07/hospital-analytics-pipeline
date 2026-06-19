-- Create a read-only user for the AI agent
CREATE USER sql_agent WITH PASSWORD 'happy_ai';

-- Allow connection to the database
GRANT CONNECT ON DATABASE hospital_management TO sql_agent;

-- Allow usage of the harmonized schema only
GRANT USAGE ON SCHEMA harmonized TO sql_agent;

-- Allow SELECT only on existing harmonized tables
GRANT SELECT ON ALL TABLES IN SCHEMA harmonized TO sql_agent;

-- Allow SELECT on future harmonized tables
ALTER DEFAULT PRIVILEGES IN SCHEMA harmonized
GRANT SELECT ON TABLES TO sql_agent;