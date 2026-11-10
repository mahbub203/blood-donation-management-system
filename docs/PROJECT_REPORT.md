# Academic Project Report
## Blood Donation Management System (BDMS) — LifeDrop BD

**University Course:** Database Management Systems (DBMS)  
**Project Title:** LifeDrop BD — Centralized Blood Donation Management System  
**Tagline:** Every Drop Counts. Every Life Matters.  
**Platform Stack:** Python 3.15, Django 6.1, PostgreSQL 16, Bootstrap 5, Chart.js  
**Scenario:** Nationwide Healthcare Informatics for Bangladesh  

---

## 1. Abstract
The shortage of safe blood and delays in locating compatible, medically eligible voluntary donors represent critical life-threatening challenges in emergency surgery and trauma care across Bangladesh. **LifeDrop BD** is an enterprise-grade, database-driven healthcare web application engineered to solve this crisis. Developed for an academic Database Management System (DBMS) capstone evaluation, the platform demonstrates rigorous relational database engineering in PostgreSQL 16, complete normalization up to 3NF, automated ABO/Rh red-cell compatibility engines, conservative 120-day donation interval calculations, PL/pgSQL stored procedures, audit triggers, multi-table joins, and interactive EXPLAIN ANALYZE performance profiling.

---

## 2. Problem Statement
In Bangladesh, over 900,000 to 1,000,000 units of blood are required annually. Despite this demand:
1. Blood seeking remains fragmented across social media groups without verification of donors' medical rest periods.
2. Search systems often default to naive identical blood-group matching, failing to recognize critical transfusion compatibility (e.g. O- universal red-cell donation).
3. Contact information of voluntary donors is frequently exposed to public abuse.
4. Healthcare institutions lack centralized synchronization between blood bank inventory, patient requests, and certified donor histories.

---

## 3. Project Objectives
- Engineer a normalized relational database (3NF) on PostgreSQL 16.
- Implement Role-Based Access Control (RBAC) with 4 distinct user actors: Administrator, Blood Donor, Blood Requester, and Hospital/Organization.
- Build an intelligent donor search algorithm matching donors by ABO/Rh red-cell compatibility, district, and conservative eligibility rules (120 days).
- Implement database views, stored functions, triggers, and atomic transaction blocks ensuring zero race conditions or duplicate entries.
- Deliver an accessible, responsive user interface adhering to clean healthcare aesthetics (#C62828 / #172B4D).

---

## 4. User Roles & System Permissions

| Role | Permissions & Operational Scope |
| :--- | :--- |
| **Administrator** | Global oversight: manages all user accounts, activates/suspends users, verifies hospital DGHS licenses, oversees request lifecycles, inspects audit logs, generates CSV/printable reports. |
| **Blood Donor** | Donor portal: updates availability with one-click toggle, views eligibility countdown timer, inspects compatible requests, tracks personal donation history. |
| **Blood Requester** | Requester portal: submits emergency blood requests with hospital and urgency levels, monitors status updates, views matching donors. |
| **Hospital / Organization** | Healthcare portal: creates clinical blood requests, coordinates patient appointments, certifies completed whole-blood collections. |

---

## 5. Relational Database & Advanced PostgreSQL Architecture

### 5.1 Third Normal Form (3NF) Compliance
- Atomic fields across all relations eliminate compound attributes.
- Geographic hierarchy (`District` and `Upazila`) eliminates transitive dependencies.
- Blood transfusion logic is normalized into a relational compatibility matrix (`core_bloodcompatibility`).

### 5.2 Database Integrity & Constraints
- `chk_blood_request_units_needed_positive`: Enforces `units_needed > 0`.
- `chk_donation_units_positive`: Enforces `units_donated > 0`.
- `unique_completed_donation_per_day`: Unique constraint preventing duplicate certified donations for a donor on the same date.
- `on_delete=models.PROTECT` on `BloodGroup` prevents accidental deletion of clinical categories.

### 5.3 PostgreSQL Views
- `view_available_eligible_donors`: Evaluates eligibility dynamically using PostgreSQL date arithmetic (`CURRENT_DATE - last_donation_date >= 120`).
- `view_blood_request_summary`: Computes real-time matched donor counts via correlated subqueries.
- `view_district_donation_stats`: Aggregates district-level donor supply and patient demand.

### 5.4 Stored Procedures & Triggers
- **Function:** `fn_certify_completed_donation(p_donation_id, p_verifier_id, p_remarks)` executes atomic transitions across donation records, donor profiles, and blood request statuses.
- **Trigger:** `trg_audit_request_status` captures all blood request status updates and writes immutable records into `analytics_activitylog`.

---

## 6. Testing & Quality Assurance
The test suite consists of 12 comprehensive automated tests executed directly against PostgreSQL:
1. `test_user_login_success` (Authentication & password hashing)
2. `test_role_based_dashboard_redirects` (RBAC access boundaries)
3. `test_unauthorized_admin_access_restricted` (Security isolation)
4. `test_donation_eligibility_120_days_rule` (Conservative interval validation)
5. `test_donor_availability_toggle` (State persistence)
6. `test_intelligent_abo_compatibility_search` (ABO/Rh compatibility logic)
7. `test_create_blood_request` (Request generation & validation)
8. `test_cancel_blood_request` (Lifecycle handling)
9. `test_certify_completed_donation_updates_all_records` (Procedure & atomic transaction)
10. `test_database_constraint_prevents_duplicate_completed_donation_same_day` (PostgreSQL unique constraint)
11. `test_chk_blood_request_units_needed_positive_constraint` (PostgreSQL check constraint)
12. `test_postgresql_view_execution` (Relational view schema verification)

---

## 7. Conclusion
**LifeDrop BD** demonstrates how relational database architecture, rigorous normalization, and robust query design can be combined with modern full-stack web engineering to solve urgent real-world problems. The system fulfills all criteria of an advanced DBMS course project, providing a locally runnable, professionally documented platform ready for academic defense.
