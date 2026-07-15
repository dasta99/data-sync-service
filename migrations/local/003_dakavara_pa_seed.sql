-- dakavara_pa seed data matching production structure

USE dakavara_pa;

-- State
INSERT INTO state (state_id, state_name) VALUES (1, 'Andhra Pradesh'), (36, 'Telangana');

-- Parliament constituencies (dakavara_pa.constituency where location_scope_id=10)
INSERT INTO constituency (constituency_id, name, state_id, parliament_id) VALUES
    (101, 'Araku', 1, 101), (102, 'Srikakulam', 1, 102), (103, 'Vizianagaram', 1, 103),
    (104, 'Visakhapatnam', 1, 104), (105, 'Anakapalli', 1, 105), (106, 'Kakinada', 1, 106),
    (107, 'Amalapuram', 1, 107), (108, 'Narasapur', 1, 108), (109, 'Eluru', 1, 109),
    (110, 'Machilipatnam', 1, 110), (111, 'Vijayawada', 1, 111), (112, 'Guntur', 1, 112),
    (113, 'Narasaraopet', 1, 113), (114, 'Bapatla', 1, 114), (115, 'Ongole', 1, 115),
    (116, 'Nandyal', 1, 116), (117, 'Kurnool', 1, 117), (118, 'Anantapur', 1, 118),
    (119, 'Hindupur', 1, 119), (120, 'Kadiri', 1, 120);

-- Assembly constituencies (location_scope_id=4)
INSERT INTO constituency (constituency_id, name, state_id, parliament_id) VALUES
    (1001, 'Araku Valley', 1, 101), (1002, 'Paderu', 1, 101),
    (1003, 'Srikakulam', 1, 102), (1004, 'Amadalavalasa', 1, 102),
    (1005, 'Vizianagaram', 1, 103), (1006, 'Bobbili', 1, 103),
    (1007, 'Visakhapatnam East', 1, 104), (1008, 'Visakhapatnam West', 1, 104),
    (1009, 'Gajuwaka', 1, 104), (1010, 'Anakapalli', 1, 105),
    (1011, 'Kakinada Rural', 1, 106), (1012, 'Kakinada City', 1, 106),
    (1013, 'Amalapuram', 1, 107), (1014, 'Razole', 1, 107),
    (1015, 'Narasapur', 1, 108), (1016, 'Bhimavaram', 1, 108),
    (1017, 'Eluru', 1, 109), (1018, 'Unguturu', 1, 109),
    (1019, 'Machilipatnam', 1, 110), (1020, 'Gannavaram', 1, 110);

-- Tehsil (location_scope_id=5)
INSERT INTO tehsil (tehsil_id, tehsil_name, constituency_id) VALUES
    (2001, 'Araku', 1001), (2002, 'Paderu', 1002),
    (2003, 'Srikakulam Rural', 1003), (2004, 'Amadalavalasa', 1004),
    (2005, 'Vizianagaram Rural', 1005), (2006, 'Bobbili', 1006),
    (2007, 'Gajuwaka', 1009), (2008, 'Anakapalli', 1010),
    (2009, 'Kakinada Rural', 1011), (2010, 'Kakinada City', 1012),
    (2011, 'Amalapuram', 1013), (2012, 'Razole', 1014),
    (2013, 'Narasapur', 1015), (2014, 'Bhimavaram', 1016),
    (2015, 'Eluru', 1017), (2016, 'Unguturu', 1018),
    (2017, 'Machilipatnam', 1019), (2018, 'Gannavaram', 1020);

-- Panchayat (location_scope_id=6)
INSERT INTO panchayat (panchayat_id, panchayat_name, tehsil_id) VALUES
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

-- Local election bodies / Towns (location_scope_id=7)
INSERT INTO local_election_body (local_election_body_id, name, constituency_id) VALUES
    (4001, 'Araku Town', 1001), (4002, 'Paderu Town', 1002),
    (4003, 'Srikakulam Town', 1003), (4004, 'Amadalavalasa Town', 1004),
    (4005, 'Vizianagaram Town', 1005), (4006, 'Bobbili Town', 1006),
    (4007, 'Gajuwaka Town', 1009), (4008, 'Anakapalli Town', 1010),
    (4009, 'Kakinada Town', 1012), (4010, 'Amalapuram Town', 1013),
    (4011, 'Narasapur Town', 1015), (4012, 'Bhimavaram Town', 1016),
    (4013, 'Eluru Town', 1017), (4014, 'Machilipatnam Town', 1019),
    (4015, 'Gannavaram Town', 1020);

-- Booths (location_scope_id=9)
INSERT INTO booth (booth_id, part_no, constituency_id, panchayat_id, publication_date_id)
SELECT
    CONCAT('B', LPAD(n, 4, '0')),
    CONCAT('Part ', ((n - 1) MOD 3) + 1),
    1001 + ((n - 1) MOD 20),
    3001 + ((n - 1) MOD 36),
    42
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
) numbers;

-- Clusters (location_scope_id=17)
INSERT INTO cluster (cluster_id, cluster_name, constituency_id) VALUES
    (5001, 'Araku Cluster 1', 1001), (5002, 'Paderu Cluster 1', 1002),
    (5003, 'Srikakulam Cluster 1', 1003), (5004, 'Amadalavalasa Cluster 1', 1004),
    (5005, 'Vizianagaram Cluster 1', 1005), (5006, 'Bobbili Cluster 1', 1006),
    (5007, 'Gajuwaka Cluster 1', 1009), (5008, 'Anakapalli Cluster 1', 1010),
    (5009, 'Kakinada Rural Cluster 1', 1011), (5010, 'Kakinada City Cluster 1', 1012),
    (5011, 'Amalapuram Cluster 1', 1013), (5012, 'Razole Cluster 1', 1014),
    (5013, 'Narasapur Cluster 1', 1015), (5014, 'Bhimavaram Cluster 1', 1016),
    (5015, 'Eluru Cluster 1', 1017), (5016, 'Unguturu Cluster 1', 1018),
    (5017, 'Machilipatnam Cluster 1', 1019), (5018, 'Gannavaram Cluster 1', 1020);

-- Cluster-Booth mapping (3 booths per cluster)
INSERT INTO cluster_booth (cluster_id, booth_id)
SELECT
    5000 + ((n - 1) DIV 3) + 1,
    CONCAT('B', LPAD(n, 4, '0'))
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
) numbers;

-- Units (location_scope_id=18)
INSERT INTO unit (unit_id, unit_name, constituency_id) VALUES
    (6001, 'Araku Unit 1', 1001), (6002, 'Paderu Unit 1', 1002),
    (6003, 'Srikakulam Unit 1', 1003), (6004, 'Amadalavalasa Unit 1', 1004),
    (6005, 'Vizianagaram Unit 1', 1005), (6006, 'Bobbili Unit 1', 1006),
    (6007, 'Gajuwaka Unit 1', 1009), (6008, 'Anakapalli Unit 1', 1010),
    (6009, 'Kakinada Rural Unit 1', 1011), (6010, 'Kakinada City Unit 1', 1012),
    (6011, 'Amalapuram Unit 1', 1013), (6012, 'Razole Unit 1', 1014),
    (6013, 'Narasapur Unit 1', 1015), (6014, 'Bhimavaram Unit 1', 1016),
    (6015, 'Eluru Unit 1', 1017), (6016, 'Unguturu Unit 1', 1018),
    (6017, 'Machilipatnam Unit 1', 1019), (6018, 'Gannavaram Unit 1', 1020);

-- Unit-Booth mapping (3 booths per unit)
INSERT INTO unit_booth (unit_id, booth_id)
SELECT
    6000 + ((n - 1) DIV 3) + 1,
    CONCAT('B', LPAD(n, 4, '0'))
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
) numbers;

-- Voter info per state (location_scope_id=2)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT 1, 2, state_id, 42, 50000 FROM state;

-- Voter info per parliament (location_scope_id=10)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 10, constituency_id, 42, 5000 FROM constituency WHERE constituency_id BETWEEN 101 AND 120;

-- Voter info per assembly (location_scope_id=4)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 4, constituency_id, 42, 2500 FROM constituency WHERE constituency_id BETWEEN 1001 AND 1020;

-- Voter info per tehsil (location_scope_id=5)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 5, tehsil_id, 42, 1200 FROM tehsil;

-- Voter info per panchayat (location_scope_id=6)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT t.constituency_id, 6, p.panchayat_id, 42, 600 FROM panchayat p JOIN tehsil t ON p.tehsil_id = t.tehsil_id;

-- Voter info per town (location_scope_id=7)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 7, local_election_body_id, 42, 800 FROM local_election_body;

-- Voter info per booth (location_scope_id=9)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 9, CAST(SUBSTRING(booth_id, 2) AS UNSIGNED), 42, 300 FROM booth;

-- Voter info per cluster (location_scope_id=17)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 17, cluster_id, 42, 1000 FROM cluster;

-- Voter info per unit (location_scope_id=18)
INSERT INTO voter_info (constituency_id, location_scope_id, report_level_value, publication_date_id, total_voters)
SELECT constituency_id, 18, unit_id, 42, 1000 FROM unit;

-- TDP Committee levels
INSERT INTO tdp_committee_level (tdp_committee_level_id, tdp_committee_level) VALUES
    (15, 'Booth Level'), (16, 'Unit Level'), (17, 'Cluster Level');

-- TDP Roles
INSERT INTO tdp_roles (tdp_roles_id, role, `order`) VALUES
    (1, 'President', 1), (2, 'Secretary', 2), (3, 'Treasurer', 3);

-- TDP Committees (booth/unit/cluster level per assembly)
INSERT INTO tdp_committee (tdp_committee_level_id, tdp_committee_level_value, tdp_committee_enrollment_id, address_id)
SELECT 15, CAST(SUBSTRING(booth_id, 2) AS UNSIGNED), 4, NULL FROM booth;
INSERT INTO tdp_committee (tdp_committee_level_id, tdp_committee_level_value, tdp_committee_enrollment_id, address_id)
SELECT 16, unit_id, 4, NULL FROM unit;
INSERT INTO tdp_committee (tdp_committee_level_id, tdp_committee_level_value, tdp_committee_enrollment_id, address_id)
SELECT 17, cluster_id, 4, NULL FROM cluster;

-- TDP Cadre members (2 per committee)
INSERT INTO tdp_cadre (membership_id, first_name, mobile_no, address_id)
SELECT
    1000 + n,
    CONCAT('Member ', n),
    CONCAT('9', LPAD(FLOOR(RAND(n) * 1000000000), 9, '0')),
    NULL
FROM (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
    UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
    UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
    UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
    UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24 UNION SELECT 25
    UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29 UNION SELECT 30
    UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34 UNION SELECT 35
    UNION SELECT 36
) numbers;

-- Committee roles and members (2 per committee)
INSERT INTO tdp_committee_role (tdp_committee_id, tdp_roles_id, role, `order`)
SELECT tc.tdp_committee_id, 1, 'President', 1 FROM tdp_committee tc;
INSERT INTO tdp_committee_role (tdp_committee_id, tdp_roles_id, role, `order`)
SELECT tc.tdp_committee_id, 2, 'Secretary', 2 FROM tdp_committee tc;

INSERT INTO tdp_committee_member (tdp_committee_role_id, tdp_cadre_id, is_active)
SELECT tcr.tdp_committee_role_id, c.tdp_cadre_id, 'Y'
FROM tdp_committee_role tcr
JOIN tdp_cadre c ON c.tdp_cadre_id = (
    SELECT tdp_cadre_id FROM tdp_cadre WHERE tdp_cadre_id <= (SELECT COUNT(*) FROM tdp_committee_role)
    ORDER BY tdp_cadre_id
    LIMIT 1
    OFFSET (SELECT FIELD(tcr2.tdp_committee_role_id, (SELECT tdp_committee_role_id FROM tdp_committee_role ORDER BY tdp_committee_role_id)) - 1)
);
