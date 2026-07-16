-- Extract configs for all tables needed by transforms
-- mytdp tables (source_name = 'local')

INSERT INTO mytdp.sync_config (table_name, source_name, source_table, dest_table, enabled, poll_interval, batch_size, watermark_column, primary_key)
VALUES 
  ('booth', 'local', 'booth', 'mytdp.booth', 1, 300, 500, 'id', 'id'),
  ('assembly', 'local', 'assembly', 'mytdp.assembly', 1, 300, 500, 'id', 'id'),
  ('parliament', 'local', 'parliament', 'mytdp.parliament', 1, 300, 500, 'id', 'id'),
  ('state', 'local', 'state', 'mytdp.state', 1, 300, 500, 'id', 'id'),
  ('mytdp_cluster', 'local', 'cluster', 'mytdp.cluster', 1, 300, 500, 'id', 'id'),
  ('mytdp_unit', 'local', 'unit', 'mytdp.unit', 1, 300, 500, 'id', 'id'),
  ('sir_form_counts', 'local', 'sir_form_counts', 'mytdp.sir_form_counts', 1, 60, 500, 'id', 'id')
ON DUPLICATE KEY UPDATE enabled = 1;

-- dakavara_pa tables (source_name = 'dakavara_pa')

INSERT INTO mytdp.sync_config (table_name, source_name, source_table, dest_table, enabled, poll_interval, batch_size, watermark_column, primary_key)
VALUES 
  ('dp_state', 'dakavara_pa', 'state', 'dakavara_pa.state', 1, 300, 500, 'state_id', 'state_id'),
  ('dp_constituency', 'dakavara_pa', 'constituency', 'dakavara_pa.constituency', 1, 300, 500, 'constituency_id', 'constituency_id'),
  ('dp_tehsil', 'dakavara_pa', 'tehsil', 'dakavara_pa.tehsil', 1, 300, 500, 'tehsil_id', 'tehsil_id'),
  ('dp_panchayat', 'dakavara_pa', 'panchayat', 'dakavara_pa.panchayat', 1, 300, 500, 'panchayat_id', 'panchayat_id'),
  ('dp_local_election_body', 'dakavara_pa', 'local_election_body', 'dakavara_pa.local_election_body', 1, 300, 500, 'local_election_body_id', 'local_election_body_id'),
  ('dp_booth', 'dakavara_pa', 'booth', 'dakavara_pa.booth', 1, 300, 500, 'booth_id', 'booth_id'),
  ('dp_cluster', 'dakavara_pa', 'cluster', 'dakavara_pa.cluster', 1, 300, 500, 'cluster_id', 'cluster_id'),
  ('dp_cluster_booth', 'dakavara_pa', 'cluster_booth', 'dakavara_pa.cluster_booth', 1, 300, 500, 'cluster_id', 'cluster_id'),
  ('dp_unit', 'dakavara_pa', 'unit', 'dakavara_pa.unit', 1, 300, 500, 'unit_id', 'unit_id'),
  ('dp_unit_booth', 'dakavara_pa', 'unit_booth', 'dakavara_pa.unit_booth', 1, 300, 500, 'unit_id', 'unit_id'),
  ('dp_voter_info', 'dakavara_pa', 'voter_info', 'dakavara_pa.voter_info', 1, 300, 500, 'id', 'id'),
  ('dp_user_address', 'dakavara_pa', 'user_address', 'dakavara_pa.user_address', 1, 300, 500, 'user_address_id', 'user_address_id'),
  ('dp_tdp_cadre', 'dakavara_pa', 'tdp_cadre', 'dakavara_pa.tdp_cadre', 1, 300, 500, 'tdp_cadre_id', 'tdp_cadre_id'),
  ('dp_tdp_committee_level', 'dakavara_pa', 'tdp_committee_level', 'dakavara_pa.tdp_committee_level', 1, 300, 500, 'tdp_committee_level_id', 'tdp_committee_level_id'),
  ('dp_tdp_committee', 'dakavara_pa', 'tdp_committee', 'dakavara_pa.tdp_committee', 1, 300, 500, 'tdp_committee_id', 'tdp_committee_id'),
  ('dp_tdp_committee_role', 'dakavara_pa', 'tdp_committee_role', 'dakavara_pa.tdp_committee_role', 1, 300, 500, 'tdp_committee_role_id', 'tdp_committee_role_id'),
  ('dp_tdp_committee_member', 'dakavara_pa', 'tdp_committee_member', 'dakavara_pa.tdp_committee_member', 1, 300, 500, 'tdp_committee_role_id', 'tdp_committee_role_id'),
  ('dp_tdp_roles', 'dakavara_pa', 'tdp_roles', 'dakavara_pa.tdp_roles', 1, 300, 500, 'tdp_roles_id', 'tdp_roles_id')
ON DUPLICATE KEY UPDATE enabled = 1;
