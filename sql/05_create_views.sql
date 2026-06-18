-- ============================================================
-- Analytics schema
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- View: Appointments by status
-- ============================================================

-- Purpose:
-- This view summarizes the number of appointments by appointment status.
--
-- This is the only analytics view provided by the instructor.
-- Students should create additional analytics views as part of their project.
CREATE OR REPLACE VIEW analytics.vw_appointments_by_status AS
SELECT
    status,
    COUNT(*) AS total_appointments
FROM harmonized.appointments
GROUP BY status
ORDER BY total_appointments DESC;


-- ============================================================
-- Manual test
-- ============================================================

SELECT *
FROM analytics.vw_appointments_by_status;