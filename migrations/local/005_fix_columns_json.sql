-- Fix columns_json to proper JSON array format

UPDATE mytdp.sync_config SET columns_json = '["id","booth_id","name","part_no","assembly_id","parliament_id","publication_id","panchayat_id","mandal_id","town_id","cluster_id","unit_id","state_id"]' WHERE table_name = 'booth';
UPDATE mytdp.sync_config SET columns_json = '["id","name","parliament_id","state_id"]' WHERE table_name = 'assembly';
UPDATE mytdp.sync_config SET columns_json = '["id","name","state_id"]' WHERE table_name = 'parliament';
UPDATE mytdp.sync_config SET columns_json = '["id","state_name"]' WHERE table_name = 'state';
UPDATE mytdp.sync_config SET columns_json = '["id","cluster_name","assembly_id"]' WHERE table_name = 'mytdp_cluster';
UPDATE mytdp.sync_config SET columns_json = '["id","unit_name","assembly_id"]' WHERE table_name = 'mytdp_unit';
UPDATE mytdp.sync_config SET columns_json = '["id","verification_date","booth_id","verified_voters","active_users","available_count","temporary_shift_count","permanent_shift_count","death_count","duplicate_count","double_count","form_submitted_to_blo","blo_digitized","inserted_time"]' WHERE table_name = 'sir_verification_info';
UPDATE mytdp.sync_config SET columns_json = '["id","booth_id","user_id","role_id","forms_distributed","forms_received","created_at","updated_at"]' WHERE table_name = 'sir_form_counts';

UPDATE mytdp.sync_config SET columns_json = '["state_id","state_name"]' WHERE table_name = 'dp_state';
UPDATE mytdp.sync_config SET columns_json = '["constituency_id","name","state_id","parliament_id"]' WHERE table_name = 'dp_constituency';
UPDATE mytdp.sync_config SET columns_json = '["tehsil_id","tehsil_name","constituency_id"]' WHERE table_name = 'dp_tehsil';
UPDATE mytdp.sync_config SET columns_json = '["panchayat_id","panchayat_name","tehsil_id"]' WHERE table_name = 'dp_panchayat';
UPDATE mytdp.sync_config SET columns_json = '["local_election_body_id","name","constituency_id"]' WHERE table_name = 'dp_local_election_body';
UPDATE mytdp.sync_config SET columns_json = '["booth_id","part_no","constituency_id","panchayat_id","local_election_body_id","publication_date_id"]' WHERE table_name = 'dp_booth';
UPDATE mytdp.sync_config SET columns_json = '["cluster_id","cluster_name","constituency_id","is_deleted"]' WHERE table_name = 'dp_cluster';
UPDATE mytdp.sync_config SET columns_json = '["cluster_id","booth_id","is_deleted"]' WHERE table_name = 'dp_cluster_booth';
UPDATE mytdp.sync_config SET columns_json = '["unit_id","unit_name","constituency_id","is_deleted"]' WHERE table_name = 'dp_unit';
UPDATE mytdp.sync_config SET columns_json = '["unit_id","booth_id","is_deleted"]' WHERE table_name = 'dp_unit_booth';
UPDATE mytdp.sync_config SET columns_json = '["id","constituency_id","location_scope_id","report_level_value","publication_date_id","total_voters"]' WHERE table_name = 'dp_voter_info';
UPDATE mytdp.sync_config SET columns_json = '["user_address_id","constituency_id","tehsil_id","local_election_body","booth_id","unit_id","cluster_id"]' WHERE table_name = 'dp_user_address';
UPDATE mytdp.sync_config SET columns_json = '["tdp_cadre_id","membership_id","first_name","mobile_no","address_id","is_deleted"]' WHERE table_name = 'dp_tdp_cadre';
UPDATE mytdp.sync_config SET columns_json = '["tdp_committee_level_id","tdp_committee_level"]' WHERE table_name = 'dp_tdp_committee_level';
UPDATE mytdp.sync_config SET columns_json = '["tdp_committee_id","tdp_committee_level_id","tdp_committee_level_value","tdp_committee_enrollment_id","address_id","is_deleted"]' WHERE table_name = 'dp_tdp_committee';
UPDATE mytdp.sync_config SET columns_json = '["tdp_committee_role_id","tdp_committee_id","tdp_roles_id","role","order"]' WHERE table_name = 'dp_tdp_committee_role';
UPDATE mytdp.sync_config SET columns_json = '["tdp_committee_role_id","tdp_cadre_id","is_active"]' WHERE table_name = 'dp_tdp_committee_member';
UPDATE mytdp.sync_config SET columns_json = '["tdp_roles_id","role","order"]' WHERE table_name = 'dp_tdp_roles';
