-- Hospital Patient Record System SQL Script

-- Drop old database if exists
DROP DATABASE IF EXISTS hospital_system;
CREATE DATABASE hospital_system;
USE hospital_system;

-------------------------------------------------
-- 1. TABLE CREATION
-------------------------------------------------

-- Patient Table
CREATE TABLE patient (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL CHECK (age >= 0),
    gender ENUM('Male','Female','Other') CHECK (gender IN ('Male','Female','Other')),
    city VARCHAR(50) DEFAULT 'Unknown'
);

-- Doctor Table
CREATE TABLE doctor (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL
);

-- Appointment Table
CREATE TABLE appointment (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id) ON DELETE CASCADE
);

-------------------------------------------------
-- 2. SAMPLE DATA INSERTION
-------------------------------------------------

-- Patients
INSERT INTO patient (name, age, gender, city) VALUES
('Arun Kumar', 25, 'Male', 'Chennai'),
('Priya Sharma', 30, 'Female', 'Bangalore'),
('Ravi Patel', 45, 'Male', 'Mumbai'),
('Anjali Mehta', 22, 'Female', 'Delhi'),
('Karthik R', 60, 'Male', 'Hyderabad'),
('Divya Singh', 35, 'Female', 'Pune'),
('Mohit Jain', 50, 'Male', 'Kolkata'),
('Sneha Iyer', 28, 'Female', 'Chennai'),
('Rahul Verma', 40, 'Male', 'Delhi'),
('Lakshmi Nair', 55, 'Female', 'Trivandrum');

-- Doctors
INSERT INTO doctor (name, specialization) VALUES
('Dr. Rajesh Kumar', 'Cardiologist'),
('Dr. Neha Gupta', 'Dermatologist'),
('Dr. Suresh R', 'Orthopedic'),
('Dr. Pooja Sharma', 'Neurologist'),
('Dr. Anil Kumar', 'General Physician'),
('Dr. Ramesh Singh', 'ENT Specialist'),
('Dr. Kavita Mehta', 'Gynecologist'),
('Dr. Manoj Jain', 'Pediatrician'),
('Dr. Shweta Verma', 'Psychiatrist'),
('Dr. Ajay Nair', 'Dentist');

-- Appointments
INSERT INTO appointment (patient_id, doctor_id, appointment_date) VALUES
(1, 1, '2025-10-05'),
(2, 2, '2025-10-06'),
(3, 3, '2025-10-07'),
(4, 1, '2025-10-08'),
(5, 4, '2025-10-09'),
(6, 5, '2025-10-10'),
(7, 6, '2025-10-11'),
(8, 7, '2025-10-12'),
(9, 8, '2025-10-13'),
(10, 9, '2025-10-14');

-------------------------------------------------
-- 3. SIMPLE SELECT QUERIES
-------------------------------------------------
SELECT * FROM patient;
SELECT * FROM doctor;
SELECT * FROM appointment;
SELECT name, city FROM patient;
SELECT name, specialization FROM doctor;

-------------------------------------------------
-- 4. WHERE + ORDER BY QUERIES
-------------------------------------------------
SELECT * FROM patient WHERE city = 'Chennai';
SELECT * FROM doctor WHERE specialization = 'Cardiologist';
SELECT * FROM patient WHERE age > 40 ORDER BY age DESC;
SELECT * FROM appointment WHERE appointment_date >= '2025-10-10';
SELECT * FROM patient WHERE gender = 'Female' ORDER BY name ASC;

-------------------------------------------------
-- 5. AGGREGATE FUNCTIONS
-------------------------------------------------
SELECT COUNT(*) AS total_patients FROM patient;
SELECT AVG(age) AS avg_age FROM patient;
SELECT doctor_id, COUNT(*) AS total_appointments FROM appointment GROUP BY doctor_id;
SELECT city, COUNT(*) AS patients_per_city FROM patient GROUP BY city;
SELECT MAX(age) AS oldest_patient FROM patient;

-------------------------------------------------
-- 6. JOINS
-------------------------------------------------
SELECT a.appointment_id, p.name AS patient_name, d.name AS doctor_name, a.appointment_date
FROM appointment a
JOIN patient p ON a.patient_id = p.patient_id
JOIN doctor d ON a.doctor_id = d.doctor_id;

-------------------------------------------------
-- 7. SUBQUERIES
-------------------------------------------------
-- Patients who have more than 1 appointment
SELECT name FROM patient WHERE patient_id IN (
    SELECT patient_id FROM appointment GROUP BY patient_id HAVING COUNT(*) > 1
);

-- Most consulted doctor
SELECT name FROM doctor WHERE doctor_id = (
    SELECT doctor_id FROM appointment GROUP BY doctor_id ORDER BY COUNT(*) DESC LIMIT 1
);

-------------------------------------------------
-- 8. CASE EXPRESSION
-------------------------------------------------
SELECT name, age,
    CASE 
        WHEN age < 18 THEN 'Child'
        WHEN age BETWEEN 18 AND 59 THEN 'Adult'
        ELSE 'Senior'
    END AS age_group
FROM patient;

-------------------------------------------------
-- 9. VIEW CREATION
-------------------------------------------------
CREATE OR REPLACE VIEW appointment_details AS
SELECT a.appointment_id, p.name AS patient_name, d.name AS doctor_name, a.appointment_date
FROM appointment a
JOIN patient p ON a.patient_id = p.patient_id
JOIN doctor d ON a.doctor_id = d.doctor_id;

SELECT * FROM appointment_details;

-------------------------------------------------
-- 10. INDEX CREATION
-------------------------------------------------
CREATE INDEX idx_patient_city ON patient(city);
CREATE INDEX idx_doctor_specialization ON doctor(specialization);

-------------------------------------------------
-- 11. STORED PROCEDURE & FUNCTION
-------------------------------------------------

-- Stored Procedure: Get appointments for a given doctor
DELIMITER //
CREATE PROCEDURE GetDoctorAppointments(IN doc_id INT)
BEGIN
    SELECT a.appointment_id, p.name AS patient_name, a.appointment_date
    FROM appointment a
    JOIN patient p ON a.patient_id = p.patient_id
    WHERE a.doctor_id = doc_id;
END //
DELIMITER ;

-- Function: Count appointments for a doctor
DELIMITER //
CREATE FUNCTION CountAppointments(doc_id INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT;
    SELECT COUNT(*) INTO total FROM appointment WHERE doctor_id = doc_id;
    RETURN total;
END //
DELIMITER ;

-------------------------------------------------
-- 12. TRANSACTIONS
-------------------------------------------------
START TRANSACTION;

-- Insert a new patient and appointment
INSERT INTO patient (name, age, gender, city) VALUES ('Test User', 33, 'Male', 'Chennai');
INSERT INTO appointment (patient_id, doctor_id, appointment_date)
VALUES (LAST_INSERT_ID(), 2, '2025-10-15');

-- Rollback example
-- ROLLBACK;

-- Commit example
COMMIT;
