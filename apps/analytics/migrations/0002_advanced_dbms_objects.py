from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('donations', '0001_initial'),
        ('blood_requests', '0001_initial'),
        ('donors', '0001_initial'),
        ('core', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # 1. View: Available & Eligible Donors View
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW view_available_eligible_donors AS
            SELECT 
                dp.id AS donor_profile_id,
                u.id AS user_id,
                u.first_name || ' ' || u.last_name AS full_name,
                u.phone_number,
                bg.id AS blood_group_id,
                bg.name AS blood_group,
                d.id AS district_id,
                d.name AS district_name,
                d.division,
                uz.id AS upazila_id,
                uz.name AS upazila_name,
                dp.last_donation_date,
                dp.is_available,
                dp.total_donations,
                CASE 
                    WHEN dp.last_donation_date IS NULL THEN TRUE
                    WHEN CURRENT_DATE - dp.last_donation_date >= 120 THEN TRUE
                    ELSE FALSE
                END AS is_eligible,
                CASE 
                    WHEN dp.last_donation_date IS NULL THEN 0
                    WHEN CURRENT_DATE - dp.last_donation_date >= 120 THEN 0
                    ELSE 120 - (CURRENT_DATE - dp.last_donation_date)
                END AS days_remaining
            FROM donors_donorprofile dp
            JOIN accounts_user u ON dp.user_id = u.id
            JOIN core_bloodgroup bg ON dp.blood_group_id = bg.id
            LEFT JOIN core_district d ON dp.district_id = d.id
            LEFT JOIN core_upazila uz ON dp.upazila_id = uz.id
            WHERE u.is_active = TRUE AND dp.is_available = TRUE;
            """,
            reverse_sql="DROP VIEW IF EXISTS view_available_eligible_donors;"
        ),

        # 2. View: Blood Request Summary with Subquery
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW view_blood_request_summary AS
            SELECT 
                br.id AS request_id,
                br.request_code,
                br.patient_name,
                bg.name AS blood_group,
                br.units_needed,
                br.hospital_name,
                d.name AS district_name,
                br.required_date,
                br.emergency_level,
                br.status,
                br.created_at,
                u.first_name || ' ' || u.last_name AS requester_name,
                u.phone_number AS requester_phone,
                (
                    SELECT COUNT(*)
                    FROM donors_donorprofile dp2
                    JOIN core_bloodcompatibility bc ON dp2.blood_group_id = bc.donor_group_id
                    WHERE bc.recipient_group_id = br.blood_group_id
                      AND dp2.district_id = br.district_id
                      AND dp2.is_available = TRUE
                      AND (dp2.last_donation_date IS NULL OR CURRENT_DATE - dp2.last_donation_date >= 120)
                ) AS matching_eligible_donors_count
            FROM blood_requests_bloodrequest br
            JOIN core_bloodgroup bg ON br.blood_group_id = bg.id
            JOIN core_district d ON br.district_id = d.id
            JOIN accounts_user u ON br.requester_id = u.id;
            """,
            reverse_sql="DROP VIEW IF EXISTS view_blood_request_summary;"
        ),

        # 3. View: District Donation Statistics
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW view_district_donation_stats AS
            SELECT 
                d.id AS district_id,
                d.name AS district_name,
                d.division,
                COUNT(DISTINCT dp.id) AS total_donors,
                COUNT(DISTINCT CASE WHEN dp.is_available = TRUE THEN dp.id END) AS available_donors,
                COUNT(DISTINCT br.id) AS total_requests,
                COUNT(DISTINCT CASE WHEN br.status = 'FULFILLED' THEN br.id END) AS fulfilled_requests,
                COALESCE(SUM(don.units_donated), 0) AS total_units_donated
            FROM core_district d
            LEFT JOIN donors_donorprofile dp ON d.id = dp.district_id
            LEFT JOIN blood_requests_bloodrequest br ON d.id = br.district_id
            LEFT JOIN donations_donation don ON don.donor_id = dp.id AND don.status = 'COMPLETED'
            GROUP BY d.id, d.name, d.division;
            """,
            reverse_sql="DROP VIEW IF EXISTS view_district_donation_stats;"
        ),

        # 4. PL/pgSQL Function: Calculate Donor Eligibility
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION fn_calculate_donor_eligibility(p_donor_id INT)
            RETURNS TABLE(
                donor_id INT,
                is_eligible BOOLEAN,
                days_remaining INT,
                next_eligible_date DATE
            ) AS $$
            DECLARE
                v_last_date DATE;
                v_is_available BOOLEAN;
                v_days_diff INT;
            BEGIN
                SELECT last_donation_date, is_available
                INTO v_last_date, v_is_available
                FROM donors_donorprofile
                WHERE id = p_donor_id;

                IF NOT FOUND THEN
                    RETURN;
                END IF;

                IF v_last_date IS NULL THEN
                    donor_id := p_donor_id;
                    is_eligible := v_is_available;
                    days_remaining := 0;
                    next_eligible_date := CURRENT_DATE;
                    RETURN NEXT;
                ELSE
                    v_days_diff := CURRENT_DATE - v_last_date;
                    donor_id := p_donor_id;
                    IF v_days_diff >= 120 AND v_is_available THEN
                        is_eligible := TRUE;
                        days_remaining := 0;
                        next_eligible_date := CURRENT_DATE;
                    ELSE
                        is_eligible := FALSE;
                        days_remaining := GREATEST(0, 120 - v_days_diff);
                        next_eligible_date := v_last_date + INTERVAL '120 days';
                    END IF;
                    RETURN NEXT;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS fn_calculate_donor_eligibility(INT);"
        ),

        # 5. PL/pgSQL Stored Procedure: Certify Completed Donation with atomic transaction logic
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION fn_certify_completed_donation(
                p_donation_id INT,
                p_verifier_id INT,
                p_remarks TEXT
            )
            RETURNS BOOLEAN AS $$
            DECLARE
                v_donor_id INT;
                v_donation_date DATE;
                v_req_id INT;
            BEGIN
                SELECT donor_id, donation_date, blood_request_id
                INTO v_donor_id, v_donation_date, v_req_id
                FROM donations_donation
                WHERE id = p_donation_id;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Donation record % does not exist', p_donation_id;
                END IF;

                -- 1. Update donation status to COMPLETED
                UPDATE donations_donation
                SET status = 'COMPLETED',
                    verified_by_id = p_verifier_id,
                    remarks = COALESCE(remarks || ' | ', '') || p_remarks,
                    updated_at = NOW()
                WHERE id = p_donation_id;

                -- 2. Update donor profile stats
                UPDATE donors_donorprofile
                SET last_donation_date = v_donation_date,
                    total_donations = total_donations + 1,
                    updated_at = NOW()
                WHERE id = v_donor_id;

                -- 3. If tied to a blood request, fulfill it
                IF v_req_id IS NOT NULL THEN
                    UPDATE blood_requests_bloodrequest
                    SET status = 'FULFILLED',
                        updated_at = NOW()
                    WHERE id = v_req_id;
                END IF;

                -- 4. Insert activity log
                INSERT INTO analytics_activitylog(action, details, created_at, user_id)
                VALUES ('DONATION_CERTIFIED', 'Certified donation ID ' || p_donation_id || ' for donor ' || v_donor_id, NOW(), p_verifier_id);

                RETURN TRUE;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS fn_certify_completed_donation(INT, INT, TEXT);"
        ),

        # 6. Database Trigger: Audit Blood Request Status Changes
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION fn_trg_audit_request_status()
            RETURNS TRIGGER AS $$
            BEGIN
                IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
                    INSERT INTO analytics_activitylog (action, details, created_at, user_id)
                    VALUES (
                        'REQUEST_STATUS_CHANGED',
                        'Blood Request [' || NEW.request_code || '] status changed from ' || OLD.status || ' to ' || NEW.status,
                        NOW(),
                        NEW.requester_id
                    );
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_audit_request_status ON blood_requests_bloodrequest;
            CREATE TRIGGER trg_audit_request_status
            AFTER UPDATE OF status ON blood_requests_bloodrequest
            FOR EACH ROW
            EXECUTE FUNCTION fn_trg_audit_request_status();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trg_audit_request_status ON blood_requests_bloodrequest;
            DROP FUNCTION IF EXISTS fn_trg_audit_request_status();
            """
        ),
    ]
