-- Seed data matching actual production structure
-- State: Andhra Pradesh (id=1), Telangana (id=36)

INSERT INTO state (id, state_name) VALUES (1, 'Andhra Pradesh'), (36, 'Telangana');

-- Parliament constituencies
INSERT INTO parliament (id, name, state_id) VALUES
    (101, 'Araku', 1), (102, 'Srikakulam', 1), (103, 'Vizianagaram', 1),
    (104, 'Visakhapatnam', 1), (105, 'Anakapalli', 1), (106, 'Kakinada', 1),
    (107, 'Amalapuram', 1), (108, 'Narasapur', 1), (109, 'Eluru', 1),
    (110, 'Machilipatnam', 1), (111, 'Vijayawada', 1), (112, 'Guntur', 1),
    (113, 'Narasaraopet', 1), (114, 'Bapatla', 1), (115, 'Ongole', 1),
    (116, 'Nandyal', 1), (117, 'Kurnool', 1), (118, 'Anantapur', 1),
    (119, 'Hindupur', 1), (120, 'Kadiri', 1);

-- Assembly constituencies
INSERT INTO assembly (id, name, parliament_id, state_id) VALUES
    (1001, 'Araku Valley', 101, 1), (1002, 'Paderu', 101, 1),
    (1003, 'Srikakulam', 102, 1), (1004, 'Amadalavalasa', 102, 1),
    (1005, 'Vizianagaram', 103, 1), (1006, 'Bobbili', 103, 1),
    (1007, 'Visakhapatnam East', 104, 1), (1008, 'Visakhapatnam West', 104, 1),
    (1009, 'Gajuwaka', 104, 1), (1010, 'Anakapalli', 105, 1),
    (1011, 'Kakinada Rural', 106, 1), (1012, 'Kakinada City', 106, 1),
    (1013, 'Amalapuram', 107, 1), (1014, 'Razole', 107, 1),
    (1015, 'Narasapur', 108, 1), (1016, 'Bhimavaram', 108, 1),
    (1017, 'Eluru', 109, 1), (1018, 'Unguturu', 109, 1),
    (1019, 'Machilipatnam', 110, 1), (1020, 'Gannavaram', 110, 1);

-- Mandals
INSERT INTO mandal (id, name, assembly_id) VALUES
    (2001, 'Araku', 1001), (2002, 'Paderu', 1002),
    (2003, 'Srikakulam Rural', 1003), (2004, 'Amadalavalasa', 1004),
    (2005, 'Vizianagaram Rural', 1005), (2006, 'Bobbili', 1006),
    (2007, 'Gajuwaka', 1009), (2008, 'Anakapalli', 1010),
    (2009, 'Kakinada Rural', 1011), (2010, 'Kakinada City', 1012),
    (2011, 'Amalapuram', 1013), (2012, 'Razole', 1014),
    (2013, 'Narasapur', 1015), (2014, 'Bhimavaram', 1016),
    (2015, 'Eluru', 1017), (2016, 'Unguturu', 1018),
    (2017, 'Machilipatnam', 1019), (2018, 'Gannavaram', 1020);

-- Panchayats (2 per mandal)
INSERT INTO panchayat (id, name, mandal_id) VALUES
    (3001, 'Araku Panchayat', 2001), (3002, 'Valley Panchayat', 2001),
    (3003, 'Paderu Panchayat', 2002), (3004, 'Hills Panchayat', 2002),
    (3005, 'Srikakulam Panchayat', 2003), (3006, 'Coastal Panchayat', 2003),
    (3007, 'Amadalavalasa Panchayat', 2004), (3008, 'River Panchayat', 2004),
    (3009, 'Vizianagaram Panchayat', 2005), (3010, 'Fort Panchayat', 2005),
    (3011, 'Bobbili Panchayat', 2006), (3012, 'Palace Panchayat', 2006),
    (3013, 'Gajuwaka Panchayat', 2007), (3014, 'Industrial Panchayat', 2007),
    (3015, 'Anakapalli Panchayat', 2008), (3016, 'Rural Panchayat', 2008),
    (3017, 'Kakinada Panchayat', 2009), (3018, 'Port Panchayat', 2009),
    (3019, 'City Panchayat', 2010), (3020, 'Town Panchayat', 2010),
    (3021, 'Amalapuram Panchayat', 2011), (3022, 'Delta Panchayat', 2011),
    (3023, 'Razole Panchayat', 2012), (3024, 'Coast Panchayat', 2012),
    (3025, 'Narasapur Panchayat', 2013), (3026, 'River Mouth Panchayat', 2013),
    (3027, 'Bhimavaram Panchayat', 2014), (3028, 'Market Panchayat', 2014),
    (3029, 'Eluru Panchayat', 2015), (3030, 'Canal Panchayat', 2015),
    (3031, 'Unguturu Panchayat', 2016), (3032, 'Hills Panchayat 2', 2016),
    (3033, 'Machilipatnam Panchayat', 2017), (3034, 'Beach Panchayat', 2017),
    (3035, 'Gannavaram Panchayat', 2018), (3036, 'Airport Panchayat', 2018);

-- Booths (60 booths across 20 assemblies, 3 each)
INSERT INTO booth (id, booth_id, name, part_no, assembly_id, parliament_id, publication_id, panchayat_id, state_id)
SELECT
    CONCAT('B', LPAD(n, 4, '0')),
    CONCAT('B', LPAD(n, 4, '0')),
    CONCAT('Booth ', n),
    CONCAT('Part ', ((n - 1) MOD 3) + 1),
    a.id,
    a.parliament_id,
    42,
    3001 + ((n - 1) MOD 36),
    1
FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
    UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34 UNION SELECT 35
    UNION SELECT 36 UNION SELECT 37 UNION SELECT 38 UNION SELECT 39 UNION SELECT 40
    UNION SELECT 41 UNION SELECT 42 UNION SELECT 43 UNION SELECT 44 UNION SELECT 45
    UNION SELECT 46 UNION SELECT 47 UNION SELECT 48 UNION SELECT 49 UNION SELECT 50
    UNION SELECT 51 UNION SELECT 52 UNION SELECT 53 UNION SELECT 54 UNION SELECT 55
    UNION SELECT 56 UNION SELECT 57 UNION SELECT 58 UNION SELECT 59 UNION SELECT 60
) numbers
JOIN assembly a ON a.id = 1001 + ((numbers.n - 1) MOD 20);

-- Booth voters (~300 records: 5 per booth across 60 booths)
INSERT INTO booth_voter (id, booth_id, assembly_id, parliament_id, voter_id, serial_no, kss_id, sir_verified, sir_verified_by, sir_verified_role, sir_caste_category, sir_political_party_id, sir_caste_id, sir_mobile_number, sir_latitude, sir_longitude, sir_status, created_at, updated_at)
WITH RECURSIVE nums AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM nums WHERE n < 300
)
SELECT
    CONCAT('BV', LPAD(n, 5, '0')),
    CONCAT('B', LPAD(MOD(n, 60) + 1, 4, '0')),
    1001 + MOD(n, 20),
    101 + MOD(n, 20),
    CONCAT('V', LPAD(n, 5, '0')),
    n,
    CONCAT('KSS', LPAD(n, 5, '0')),
    IF(MOD(n, 3) = 0, 1, 0),
    IF(MOD(n, 3) = 0, CONCAT('User', MOD(n, 10) + 1), NULL),
    IF(MOD(n, 3) = 0, 'BLO', NULL),
    ELT(MOD(n, 4) + 1, 'SC', 'ST', 'BC', 'General'),
    CONCAT('P', LPAD(MOD(n, 5) + 1, 2, '0')),
    CONCAT('C', LPAD(MOD(n, 8) + 1, 2, '0')),
    CONCAT('9', LPAD(FLOOR(RAND(n) * 1000000000), 9, '0')),
    CONCAT('16.', LPAD(FLOOR(RAND(n) * 5000), 4, '0')),
    CONCAT('80.', LPAD(FLOOR(RAND(n) * 5000), 4, '0')),
    ELT(MOD(n, 6) + 1, 'available', 'temporary shift', 'permanent shift', 'death', 'duplicate', 'double vote'),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n) * 30) DAY),
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n) * 7) DAY)
FROM nums;

-- Seed sir_form_counts (BLO form tracking per booth per user)
INSERT INTO sir_form_counts (booth_id, user_id, role_id, forms_distributed, forms_received, created_at)
SELECT
    CONCAT('B', LPAD(MOD(n, 60) + 1, 4, '0')),
    CONCAT('User', MOD(n, 10) + 1),
    ELT(MOD(n, 3) + 1, 15, 16, 17),
    FLOOR(RAND(n) * 20) + 5,
    FLOOR(RAND(n+100) * 15) + 3,
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n) * 30) DAY)
FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
    UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34 UNION SELECT 35
    UNION SELECT 36 UNION SELECT 37 UNION SELECT 38 UNION SELECT 39 UNION SELECT 40
    UNION SELECT 41 UNION SELECT 42 UNION SELECT 43 UNION SELECT 44 UNION SELECT 45
    UNION SELECT 46 UNION SELECT 47 UNION SELECT 48 UNION SELECT 49 UNION SELECT 50
) numbers;

-- Seed daily_booth_activity (one record per active booth per day)
INSERT INTO daily_booth_activity (booth_id, activity_date, state_id)
SELECT DISTINCT
    bv.booth_id,
    DATE(bv.updated_at),
    1
FROM booth_voter bv
WHERE bv.sir_verified = 1
AND DATE(bv.updated_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);

-- Seed sir_enums_forms_booth_wise_tracking
INSERT INTO sir_enums_forms_booth_wise_tracking (booth_id, efs_distributed, efs_digitized, total_voters, created_at)
SELECT
    CONCAT('B', LPAD(MOD(n, 60) + 1, 4, '0')),
    FLOOR(RAND(n) * 50) + 10,
    FLOOR(RAND(n+200) * 30) + 5,
    FLOOR(RAND(n+300) * 500) + 200,
    DATE_SUB(NOW(), INTERVAL FLOOR(RAND(n) * 30) DAY)
FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
) numbers;

-- Seed sir_verification_info (aggregated data by booth and date)
INSERT INTO sir_verification_info (verification_date, booth_id, verified_voters, active_users, available_count, temporary_shift_count, permanent_shift_count, death_count, duplicate_count, double_count, form_submitted_to_blo, blo_digitized, inserted_time)
SELECT
    DATE(bv.updated_at),
    bv.booth_id,
    COUNT(DISTINCT bv.voter_id),
    COUNT(DISTINCT bv.sir_verified_by),
    SUM(CASE WHEN bv.sir_status = 'available' THEN 1 ELSE 0 END),
    SUM(CASE WHEN bv.sir_status = 'temporary shift' THEN 1 ELSE 0 END),
    SUM(CASE WHEN bv.sir_status = 'permanent shift' THEN 1 ELSE 0 END),
    SUM(CASE WHEN bv.sir_status = 'death' THEN 1 ELSE 0 END),
    SUM(CASE WHEN bv.sir_status = 'duplicate' THEN 1 ELSE 0 END),
    SUM(CASE WHEN bv.sir_status = 'double vote' THEN 1 ELSE 0 END),
    SUM(IFNULL(bv.form_submitted_to_blo, 0)),
    SUM(IFNULL(bv.blo_digitized, 0)),
    DATE_ADD(NOW(), INTERVAL 330 MINUTE)
FROM booth_voter bv
WHERE bv.sir_verified = 1
GROUP BY DATE(bv.updated_at), bv.booth_id;
