-- ============================================================
-- Patients
-- ============================================================

CREATE TABLE harmonized.patients (
    patient_id         VARCHAR(50),
    first_name         VARCHAR(100),
    last_name          VARCHAR(100),
    gender             VARCHAR(1),
    date_of_birth      DATE,
    contact_number     VARCHAR(20),
    address            VARCHAR(255),
    registration_date  DATE,
    insurance_provider VARCHAR(100),
    insurance_number   VARCHAR(50),
    email              VARCHAR(255),
    source_file        TEXT,
    transformed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Doctors
-- ============================================================

CREATE TABLE harmonized.doctors (
    doctor_id          VARCHAR(10),
    first_name         VARCHAR(100),
    last_name          VARCHAR(100),
    specialization     VARCHAR(150),
    phone_number       VARCHAR(50),
    years_experience   INTEGER,
    hospital_branch    VARCHAR(150),
    email              VARCHAR(150),
    source_file        TEXT,
    transformed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Appointments
-- ============================================================

CREATE TABLE harmonized.appointments (
    appointment_id     VARCHAR(10),
    patient_id         VARCHAR(10),
    doctor_id          VARCHAR(10),
    appointment_date   DATE,
    appointment_time   TIME,
    reason_for_visit   VARCHAR(255),
    status             VARCHAR(50),
    source_file        TEXT,
    transformed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Treatments
-- ============================================================

CREATE TABLE harmonized.treatments (
    treatment_id       VARCHAR(10),
    appointment_id     VARCHAR(10),
    treatment_type     VARCHAR(150),
    description        VARCHAR(255),
    treatment_date     DATE,
    source_file        TEXT,
    transformed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Billing
-- ============================================================

CREATE TABLE harmonized.billing (
    bill_id            VARCHAR(10),
    patient_id         VARCHAR(10),
    treatment_id       VARCHAR(10),
    bill_date          DATE,
    amount             NUMERIC(10,2),
    payment_method     VARCHAR(50),
    payment_status     VARCHAR(50),
    source_file        TEXT,
    transformed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Transformation procedure: Patients
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_patients()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE harmonized.patients;

    INSERT INTO harmonized.patients (
        patient_id,
        first_name,
        last_name,
        gender,
        date_of_birth,
        contact_number,
        address,
        registration_date,
        insurance_provider,
        insurance_number,
        email
    )
    SELECT
        patient_id,
        first_name,
        last_name,
        CASE
            WHEN LOWER(TRIM(gender)) = 'female' THEN 'F'
            WHEN LOWER(TRIM(gender)) = 'male' THEN 'M'
            WHEN LOWER(TRIM(gender)) = 'f' THEN 'F'
            WHEN LOWER(TRIM(gender)) = 'm' THEN 'M'
            ELSE 'O'
        END AS gender,
        TO_DATE(date_of_birth, 'DD/MM/YYYY') AS date_of_birth,
        REGEXP_REPLACE(contact_number, '[^0-9]', '', 'g') AS contact_number,
        address,
        TO_DATE(registration_date, 'DD/MM/YYYY') AS registration_date,
        insurance_provider,
        insurance_number,
        LOWER(TRIM(email)) AS email
    FROM raw.patients
    WHERE patient_id IS NOT NULL;
END;
$$;


-- ============================================================
-- Transformation procedure: Doctors
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_doctors()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE harmonized.doctors;

    INSERT INTO harmonized.doctors (
        doctor_id,
        first_name,
        last_name,
        specialization,
        phone_number,
        years_experience,
        hospital_branch,
        email
    )
    SELECT
        doctor_id,
        first_name,
        last_name,
        INITCAP(TRIM(specialization)) AS specialization,
        REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g') AS phone_number,
        NULLIF(years_experience, '')::INTEGER AS years_experience,
        hospital_branch,
        LOWER(TRIM(email)) AS email
    FROM raw.doctors
    WHERE doctor_id IS NOT NULL;
END;
$$;


-- ============================================================
-- Transformation procedure: Appointments
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_appointments()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE harmonized.appointments;

    INSERT INTO harmonized.appointments (
        appointment_id,
        patient_id,
        doctor_id,
        appointment_date,
        appointment_time,
        reason_for_visit,
        status
    )
    SELECT
        appointment_id,
        patient_id,
        doctor_id,
        TO_DATE(appointment_date, 'YYYY-MM-DD') AS appointment_date,
        CASE
            WHEN UPPER(appointment_time) LIKE '%AM%'
              OR UPPER(appointment_time) LIKE '%PM%'
            THEN TO_TIMESTAMP(appointment_time, 'HH12:MI AM')::TIME
            ELSE appointment_time::TIME
        END AS appointment_time,
        reason_for_visit,
        INITCAP(TRIM(status)) AS status
    FROM raw.appointments
    WHERE appointment_id IS NOT NULL;
END;
$$;


-- ============================================================
-- Transformation procedure: Treatments
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_treatments()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE harmonized.treatments;

    INSERT INTO harmonized.treatments (
        treatment_id,
        appointment_id,
        treatment_type,
        description,
        treatment_date
    )
    SELECT
        treatment_id,
        appointment_id,
        INITCAP(TRIM(treatment_type)) AS treatment_type,
        description,
        TO_DATE(treatment_date, 'DD/MM/YYYY') AS treatment_date
    FROM raw.treatments
    WHERE treatment_id IS NOT NULL;
END;
$$;


-- ============================================================
-- Transformation procedure: Billing
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_billing()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE harmonized.billing;

    INSERT INTO harmonized.billing (
        bill_id,
        patient_id,
        treatment_id,
        bill_date,
        amount,
        payment_method,
        payment_status
    )
    SELECT
        bill_id,
        patient_id,
        treatment_id,
        TO_DATE(bill_date, 'DD/MM/YYYY') AS bill_date,
        NULLIF(REGEXP_REPLACE(amount, '[^0-9.]', '', 'g'), '')::NUMERIC(10,2) AS amount,
        CASE
            WHEN LOWER(REPLACE(payment_method, ' ', '')) = 'insurance'
                THEN 'Insurance'
            WHEN LOWER(REPLACE(payment_method, ' ', '')) = 'creditcard'
                THEN 'Credit Card'
            WHEN LOWER(REPLACE(payment_method, ' ', '')) = 'cash'
                THEN 'Cash'
            ELSE 'Unknown'
        END AS payment_method,
        INITCAP(TRIM(payment_status)) AS payment_status
    FROM raw.billing
    WHERE bill_id IS NOT NULL;
END;
$$;


-- ============================================================
-- Master procedure
-- ============================================================

CREATE OR REPLACE PROCEDURE automation.sp_transform_all()
LANGUAGE plpgsql
AS $$
BEGIN
    CALL automation.sp_transform_patients();
    CALL automation.sp_transform_doctors();
    CALL automation.sp_transform_appointments();
    CALL automation.sp_transform_treatments();
    CALL automation.sp_transform_billing();
END;
$$;

-- ============================================================
-- Manual test
-- ============================================================

-- Before running stored procedures
SELECT COUNT(*) FROM harmonized.patients;
SELECT COUNT(*) FROM harmonized.doctors;
SELECT COUNT(*) FROM harmonized.appointments;
SELECT COUNT(*) FROM harmonized.treatments;
SELECT COUNT(*) FROM harmonized.billing;

-- Run all transformations:
CALL automation.sp_transform_all();

-- After running stored procedures
SELECT COUNT(*) FROM harmonized.patients;
SELECT COUNT(*) FROM harmonized.doctors;
SELECT COUNT(*) FROM harmonized.appointments;
SELECT COUNT(*) FROM harmonized.treatments;
SELECT COUNT(*) FROM harmonized.billing;