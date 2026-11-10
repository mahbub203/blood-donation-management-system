# LifeDrop BD — Relational Database Design Documentation

## 1. Overview
**LifeDrop BD** is an enterprise-grade Blood Donation Management System designed for the Bangladesh healthcare scenario. The database is hosted on **PostgreSQL 16** and engineered according to strict relational normalization principles up to **Third Normal Form (3NF)**.

---

## 2. Relational Schema & Entity Specifications

### 2.1 Core Entities

#### `core_district`
- `id` (PK, BigInt, Auto-increment)
- `name` (VARCHAR(100), UNIQUE, NOT NULL, Index)
- `division` (VARCHAR(50), NOT NULL, Index: Dhaka, Chittagong, Rajshahi, Khulna, Barisal, Sylhet, Rangpur, Mymensingh)
- `bn_name` (VARCHAR(100), NULLABLE)
- `created_at` (TIMESTAMP WITH TIME ZONE)

#### `core_upazila`
- `id` (PK, BigInt, Auto-increment)
- `district_id` (FK -> `core_district.id`, ON DELETE CASCADE, NOT NULL)
- `name` (VARCHAR(100), NOT NULL)
- `bn_name` (VARCHAR(100), NULLABLE)
- **Constraint:** `UNIQUE (district_id, name)`

#### `core_bloodgroup`
- `id` (PK, BigInt, Auto-increment)
- `name` (VARCHAR(5), UNIQUE, NOT NULL: `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`)
- `antigen` (VARCHAR(20))
- `antibody` (VARCHAR(20))
- `description` (TEXT)

#### `core_bloodcompatibility`
- `id` (PK, BigInt, Auto-increment)
- `donor_group_id` (FK -> `core_bloodgroup.id`, ON DELETE CASCADE)
- `recipient_group_id` (FK -> `core_bloodgroup.id`, ON DELETE CASCADE)
- `notes` (VARCHAR(255))
- **Constraint:** `UNIQUE (donor_group_id, recipient_group_id)`

---

### 2.2 Users & Authentication

#### `accounts_user` (Extends AbstractUser)
- `id` (PK, BigInt, Auto-increment)
- `username` (VARCHAR(150), UNIQUE, NOT NULL)
- `email` (VARCHAR(254), NOT NULL)
- `phone_number` (VARCHAR(20), UNIQUE, NOT NULL, Index: Bangladesh format `+8801XXXXXXXXX`)
- `role` (VARCHAR(20), NOT NULL: `ADMIN`, `DONOR`, `REQUESTER`, `HOSPITAL`)
- `is_verified` (BOOLEAN, DEFAULT FALSE)
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `date_joined` (TIMESTAMP WITH TIME ZONE)

---

### 2.3 Role Profile Extensions (1-to-1 Relationships)

#### `donors_donorprofile`
- `id` (PK, BigInt, Auto-increment)
- `user_id` (One-to-One FK -> `accounts_user.id`, ON DELETE CASCADE, UNIQUE)
- `blood_group_id` (FK -> `core_bloodgroup.id`, ON DELETE PROTECT)
- `gender` (VARCHAR(1): `M`, `F`, `O`)
- `date_of_birth` (DATE, NOT NULL)
- `district_id` (FK -> `core_district.id`, ON DELETE SET NULL, NULLABLE)
- `upazila_id` (FK -> `core_upazila.id`, ON DELETE SET NULL, NULLABLE)
- `full_address` (TEXT, NOT NULL)
- `last_donation_date` (DATE, NULLABLE, Index)
- `is_available` (BOOLEAN, DEFAULT TRUE, Index)
- `emergency_contact` (VARCHAR(20))
- `total_donations` (INTEGER, DEFAULT 0)
- **Indexes:** `idx_donor_district_avail (district_id, is_available)`, `idx_donor_blood_avail (blood_group_id, is_available)`

#### `blood_requests_requesterprofile`
- `id` (PK, BigInt, Auto-increment)
- `user_id` (One-to-One FK -> `accounts_user.id`, ON DELETE CASCADE, UNIQUE)
- `district_id` (FK -> `core_district.id`, ON DELETE SET NULL, NULLABLE)
- `upazila_id` (FK -> `core_upazila.id`, ON DELETE SET NULL, NULLABLE)
- `alternate_phone` (VARCHAR(20))
- `address` (TEXT)

#### `hospitals_hospitalorganization`
- `id` (PK, BigInt, Auto-increment)
- `user_id` (One-to-One FK -> `accounts_user.id`, ON DELETE CASCADE, UNIQUE)
- `org_name` (VARCHAR(255), NOT NULL, Index)
- `org_type` (VARCHAR(30): `HOSPITAL`, `CLINIC`, `BLOOD_BANK`, `NGO`)
- `license_number` (VARCHAR(100), UNIQUE, NOT NULL)
- `district_id` (FK -> `core_district.id`, ON DELETE PROTECT)
- `upazila_id` (FK -> `core_upazila.id`, ON DELETE SET NULL, NULLABLE)
- `address` (TEXT, NOT NULL)
- `contact_person` (VARCHAR(100))
- `phone` (VARCHAR(20), NOT NULL)
- `email` (VARCHAR(254), NOT NULL)
- `is_verified` (BOOLEAN, DEFAULT FALSE, Index)
- `verified_by_id` (FK -> `accounts_user.id`, ON DELETE SET NULL, NULLABLE)
- `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)

---

### 2.4 Operational Transactions

#### `blood_requests_bloodrequest`
- `id` (PK, BigInt, Auto-increment)
- `request_code` (VARCHAR(24), UNIQUE, NOT NULL, Index: e.g. `REQ-YYYYMMDD-XXXX`)
- `requester_id` (FK -> `accounts_user.id`, ON DELETE CASCADE)
- `patient_name` (VARCHAR(150), NOT NULL)
- `blood_group_id` (FK -> `core_bloodgroup.id`, ON DELETE PROTECT, Index)
- `units_needed` (INTEGER, NOT NULL, DEFAULT 1)
- `hospital_name` (VARCHAR(200), NOT NULL)
- `hospital_address` (TEXT, NOT NULL)
- `district_id` (FK -> `core_district.id`, ON DELETE PROTECT, Index)
- `upazila_id` (FK -> `core_upazila.id`, ON DELETE SET NULL, NULLABLE)
- `required_date` (DATE, NOT NULL, Index)
- `required_time` (TIME, NULLABLE)
- `emergency_level` (VARCHAR(20): `NORMAL`, `URGENT`, `CRITICAL`, Index)
- `contact_number` (VARCHAR(20), NOT NULL)
- `description` (TEXT, NOT NULL)
- `status` (VARCHAR(20): `PENDING`, `APPROVED`, `DONOR_FOUND`, `FULFILLED`, `REJECTED`, `CANCELLED`, Index)
- **Check Constraint:** `CHECK (units_needed > 0)`
- **Composite Indexes:** `(district_id, status)`, `(blood_group_id, status)`

#### `donations_donation`
- `id` (PK, BigInt, Auto-increment)
- `donation_code` (VARCHAR(24), UNIQUE, NOT NULL, Index)
- `donor_id` (FK -> `donors_donorprofile.id`, ON DELETE CASCADE, Index)
- `blood_request_id` (FK -> `blood_requests_bloodrequest.id`, ON DELETE SET NULL, NULLABLE)
- `donation_date` (DATE, NOT NULL, Index)
- `donation_location` (VARCHAR(255), NOT NULL)
- `blood_group_id` (FK -> `core_bloodgroup.id`, ON DELETE PROTECT)
- `units_donated` (INTEGER, NOT NULL, DEFAULT 1)
- `status` (VARCHAR(20): `SCHEDULED`, `COMPLETED`, `CANCELLED`, `REJECTED`, Index)
- `verified_by_id` (FK -> `accounts_user.id`, ON DELETE SET NULL, NULLABLE)
- `remarks` (TEXT)
- **Check Constraint:** `CHECK (units_donated > 0)`
- **Unique Constraint:** `UNIQUE (donor_id, donation_date) WHERE status = 'COMPLETED'`

#### `donations_donationappointment`
- `id` (PK, BigInt, Auto-increment)
- `donor_id` (FK -> `donors_donorprofile.id`, ON DELETE CASCADE)
- `blood_request_id` (FK -> `blood_requests_bloodrequest.id`, ON DELETE CASCADE)
- `hospital_org_id` (FK -> `hospitals_hospitalorganization.id`, ON DELETE SET NULL, NULLABLE)
- `appointment_date` (DATE, NOT NULL)
- `appointment_time` (TIME, NOT NULL)
- `status` (VARCHAR(20): `SCHEDULED`, `CONFIRMED`, `ATTENDED`, `CANCELLED`)
- `notes` (TEXT)

---

## 3. Database Normalization (Up to 3NF)

1. **First Normal Form (1NF):**
   - All columns hold atomic, scalar values (no multivalued phone arrays or comma-delimited strings).
   - Every table possesses an unambiguous primary key (`id` bigint sequence).
2. **Second Normal Form (2NF):**
   - All non-key attributes are fully functionally dependent on the entire primary key.
   - Separate tables exist for `District` and `Upazila` rather than compounding composite identifiers.
3. **Third Normal Form (3NF):**
   - Non-key columns have zero transitive dependencies.
   - Transfusion compatibility rules are decoupled into a specialized mapping relation (`core_bloodcompatibility`) rather than duplicated in donor profiles.
   - Geographic division attributes depend on `District`, not on `DonorProfile`.
