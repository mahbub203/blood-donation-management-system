# LifeDrop BD — Blood Donation Management System (BDMS)

> **"Every Drop Counts. Every Life Matters."**

A centralized, database-driven Blood Donation Management System designed for the Bangladesh healthcare ecosystem, engineered for an academic **Database Management System (DBMS)** university course project.

### 🌐 Public Live Demo
- **Live URL:** [https://indiana-pdf-titten-returned.trycloudflare.com](https://indiana-pdf-titten-returned.trycloudflare.com)
- **Academic DBMS Showcase:** [https://indiana-pdf-titten-returned.trycloudflare.com/analytics/dbms-showcase/](https://indiana-pdf-titten-returned.trycloudflare.com/analytics/dbms-showcase/)
- **GitHub Repository:** [https://github.com/mahbub203/blood-donation-management-system](https://github.com/mahbub203/blood-donation-management-system)

---

## 🌟 Key Features

### 1. 🛡️ Role-Based Access Control (RBAC)
- **Administrator:** Global management of users, requests, donations, hospitals, system logs, and executive reports.
- **Blood Donor:** Personal dashboard, 120-day eligibility countdown, one-click availability toggle, donation history, and compatible emergency alerts.
- **Blood Requester:** Emergency request posting, urgency level triage (Critical, Urgent, Normal), status tracking, and compatible donor matches.
- **Hospital / Healthcare Organization:** Verified institutional portal for creating hospital requests, coordinating appointments, and certifying donations.

### 2. 🩸 Intelligent ABO/Rh Compatibility Matching
Rather than naive identical matching, LifeDrop BD implements red-cell transfusion rules:
- **O-:** Universal red-cell donor (can donate to all 8 blood groups).
- **AB+:** Universal red-cell recipient (can receive from all 8 blood groups).
- Filters donors by district, upazila, availability, and eligibility.
- Donor contact protection: masks phone numbers for unauthenticated visitors.

### 3. 💾 Advanced PostgreSQL DBMS Implementation
- **Normalized Schema (3NF):** Elimination of insertion/deletion anomalies and transitive dependencies.
- **Database Views:** `view_available_eligible_donors`, `view_blood_request_summary`, `view_district_donation_stats`.
- **PL/pgSQL Functions:** `fn_certify_completed_donation()` with atomic transaction logic.
- **Database Triggers:** `trg_audit_request_status` for automatic audit trail logging.
- **Integrity Constraints:** CHECK constraints (`units_needed > 0`) and UNIQUE constraints preventing duplicate donations on the same day.
- **B-Tree Indexing:** High-performance index scans demonstrated via live `EXPLAIN ANALYZE`.
- **Live DBMS Showcase Page:** Interactive tab to test and view SQL queries directly on PostgreSQL.

### 4. 📊 Analytics, Reports & CSV Exports
- Real-time interactive charts powered by **Chart.js**.
- Printable report generation with clean print stylesheet.
- One-click CSV exports for Donors, Requests, and Certified Donations.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.15, Django 6.1
- **Database:** PostgreSQL 16
- **Database Connector:** psycopg 3 (binary)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3
- **Icons & Visuals:** Font Awesome 6, Chart.js
- **Form Handling:** Django Crispy Forms (Bootstrap 5 pack)
- **Testing:** Django TestCase & automated test runner

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
- Python 3.10+
- PostgreSQL 16+ (running locally on port 5432)
- Git

### 1. Clone or Open the Repository
```bash
cd blood-donation-management-system
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your PostgreSQL database credentials match in `.env`:
```env
DB_NAME=lifedrop_bd_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database & Run Migrations
Create the PostgreSQL database if not already created:
```sql
CREATE DATABASE lifedrop_bd_db;
```
Apply migrations (including tables, views, functions, and triggers):
```bash
python manage.py migrate
```

### 5. Seed Demonstration Data
Populate Bangladesh districts, upazilas, blood groups, sample donors, hospitals, requests, and donations:
```bash
python manage.py seed_data
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit: `http://127.0.0.1:8000/`

---

## 🔑 Default Demonstration Accounts

All demonstration passwords: `Admin@12345` / `Donor@12345` / `Requester@12345` / `Hospital@12345`

| Role | Username | Password | Role Description |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `Admin@12345` | Global control center, user & report management |
| **Blood Donor (O+)** | `donor_tanvir` | `Donor@12345` | Eligible donor in Dhaka |
| **Blood Donor (O-)** | `donor_rahim` | `Donor@12345` | Universal donor in Chittagong |
| **Blood Donor (B+)** | `donor_karim` | `Donor@12345` | Donated 35 days ago (Ineligible, 85 days left) |
| **Requester** | `requester_kamal` | `Requester@12345` | Patient relative with critical request |
| **Hospital** | `hospital_dmch` | `Hospital@12345` | Dhaka Medical College Hospital |

---

## 🧪 Running Automated Tests

Execute the full automated test suite covering authentication, RBAC boundaries, donor eligibility, compatibility search, request lifecycles, atomic transactions, and PostgreSQL constraints:

```bash
python manage.py test tests
```

---

## 📁 Repository Structure

```
blood-donation-management-system/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   ├── DATABASE_DESIGN.md
│   ├── SQL_QUERIES.md
│   ├── PROJECT_REPORT.md
│   └── diagrams/
│       ├── er_diagram.mmd
│       ├── system_architecture.mmd
│       └── use_case_diagram.mmd
├── lifedrop_bd/               # Project configuration
├── apps/
│   ├── core/                  # Geographics (Districts, Upazilas), compatibility matrix, landing views
│   ├── accounts/              # Custom User RBAC, authentication, profiles
│   ├── donors/                # Donor profiles, eligibility engine, ABO matching
│   ├── blood_requests/        # Blood requests, urgency triage, status lifecycle
│   ├── donations/             # Donation events, appointments, certification
│   ├── hospitals/             # Organization profiles, DGHS verification
│   ├── analytics/             # DBMS Showcase, Admin analytics, reporting, raw SQL, triggers
│   └── notifications/         # Real-time in-app notification engine
├── static/
├── templates/
└── tests/                     # Automated unit and integration test suite
```

---

## 📄 License
Academic Coursework Project — Developed for university DBMS evaluation.
