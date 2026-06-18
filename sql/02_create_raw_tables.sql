-- ============================================================
-- Patients
-- ============================================================

CREATE TABLE raw.patients (
    patient_id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    gender VARCHAR(50),
    date_of_birth VARCHAR(50),
    contact_number VARCHAR(50),
    address VARCHAR(255),
    registration_date VARCHAR(50),
    insurance_provider VARCHAR(100),
    insurance_number VARCHAR(100),
    email VARCHAR(150),
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Doctors
-- ============================================================

CREATE TABLE raw.doctors (
    doctor_id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    specialization VARCHAR(100),
    phone_number VARCHAR(50),
    years_experience VARCHAR(50),
    hospital_branch VARCHAR(100),
    email VARCHAR(150),
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Appointments
-- ============================================================

CREATE TABLE raw.appointments (
    appointment_id VARCHAR(50),
    patient_id VARCHAR(50),
    doctor_id VARCHAR(50),
    appointment_date VARCHAR(50),
    appointment_time VARCHAR(50),
    reason_for_visit VARCHAR(100),
    status VARCHAR(50),
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Treatments
-- ============================================================

CREATE TABLE raw.treatments (
    treatment_id VARCHAR(50),
    appointment_id VARCHAR(50),
    treatment_type VARCHAR(100),
    description VARCHAR(255),
    treatment_date VARCHAR(50),
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Billing
-- ============================================================

CREATE TABLE raw.billing (
    bill_id VARCHAR(50),
    patient_id VARCHAR(50),
    treatment_id VARCHAR(50),
    bill_date VARCHAR(50),
    amount VARCHAR(50),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    source_file TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);