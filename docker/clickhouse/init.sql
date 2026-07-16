-- Create test database
CREATE DATABASE IF NOT EXISTS tdp_analytics;

-- Use the database
USE tdp_analytics;

-- Create dim_booth_voter table (ClickHouse optimized)
CREATE TABLE IF NOT EXISTS dim_booth_voter (
    id String,
    booth_id String,
    voter_id String,
    assembly_id UInt32,
    parliament_id UInt32,
    serial_no UInt32,
    kss_id String,
    -- SIR fields
    sir_verified UInt8,
    sir_status String,
    sir_verified_by String,
    sir_mobile_number String,
    sir_caste_id String,
    sir_political_party_id String,
    file_path String,
    form_submitted_to_blo UInt8,
    blo_digitized UInt8,
    created_at DateTime,
    updated_at DateTime,
    -- Dimensions
    state_id UInt32,
    state_name String,
    cluster_id UInt32,
    cluster_name String,
    unit_id UInt32,
    unit_name String,
    booth_name String,
    constituency_id UInt32,
    constituency_name String
) ENGINE = MergeTree()
ORDER BY (booth_id, voter_id)
SETTINGS index_granularity = 8192;

-- Insert 100k test records
INSERT INTO dim_booth_voter
SELECT
    concat('BV', toString(number)) AS id,
    concat('B', toString(number % 60 + 1)) AS booth_id,
    concat('V', toString(number)) AS voter_id,
    1001 + (number % 20) AS assembly_id,
    101 + (number % 20) AS parliament_id,
    number AS serial_no,
    concat('KSS', toString(number)) AS kss_id,
    if(number % 3 = 0, 1, 0) AS sir_verified,
    arrayElement(['available', 'temporary shift', 'permanent shift', 'death', 'duplicate', 'double vote'], (number % 6) + 1) AS sir_status,
    if(number % 3 = 0, concat('User', toString(number % 10 + 1)), '') AS sir_verified_by,
    concat('9', toString(number % 1000000000)) AS sir_mobile_number,
    concat('C', toString(number % 8 + 1)) AS sir_caste_id,
    concat('P', toString(number % 5 + 1)) AS sir_political_party_id,
    concat('/forms/', toString(number), '.pdf') AS file_path,
    if(number % 5 = 0, 1, 0) AS form_submitted_to_blo,
    if(number % 7 = 0, 1, 0) AS blo_digitized,
    now() - INTERVAL (number % 30) DAY AS created_at,
    now() - INTERVAL (number % 7) DAY AS updated_at,
    -- Dimensions
    1 AS state_id,
    'Andhra Pradesh' AS state_name,
    1 + (number % 10) AS cluster_id,
    concat('Cluster ', toString(1 + (number % 10))) AS cluster_name,
    1 + (number % 5) AS unit_id,
    concat('Unit ', toString(1 + (number % 5))) AS unit_name,
    concat('Booth ', toString(number % 60 + 1)) AS booth_name,
    1 + (number % 5) AS constituency_id,
    concat('Constituency ', toString(1 + (number % 5))) AS constituency_name
FROM numbers(100000);

-- Verify record count
SELECT count() AS total_records FROM dim_booth_voter;

-- Create summary table: fact_booth_sir
CREATE TABLE IF NOT EXISTS fact_booth_sir (
    booth_id String,
    booth_name String,
    state_id UInt32,
    state_name String,
    parliament_id UInt32,
    assembly_id UInt32,
    cluster_id UInt32,
    cluster_name String,
    unit_id UInt32,
    unit_name String,
    constituency_id UInt32,
    constituency_name String,
    total_voters UInt64,
    verified_voters UInt64,
    active_users UInt64,
    available_count UInt64,
    temporary_shift_count UInt64,
    permanent_shift_count UInt64,
    death_count UInt64,
    duplicate_count UInt64,
    double_count UInt64,
    forms_submitted_to_blo UInt64,
    blo_digitized UInt64,
    report_date Date DEFAULT today()
) ENGINE = SummingMergeTree()
ORDER BY (booth_id, report_date);

-- Insert aggregated data
INSERT INTO fact_booth_sir
SELECT
    booth_id,
    booth_name,
    state_id,
    state_name,
    parliament_id,
    assembly_id,
    cluster_id,
    cluster_name,
    unit_id,
    unit_name,
    constituency_id,
    constituency_name,
    count(DISTINCT voter_id) AS total_voters,
    countIf(sir_verified = 1) AS verified_voters,
    countDistinct(if(sir_verified = 1, sir_verified_by, '')) AS active_users,
    countIf(sir_status = 'available') AS available_count,
    countIf(sir_status = 'temporary shift') AS temporary_shift_count,
    countIf(sir_status = 'permanent shift') AS permanent_shift_count,
    countIf(sir_status = 'death') AS death_count,
    countIf(sir_status = 'duplicate') AS duplicate_count,
    countIf(sir_status = 'double vote') AS double_count,
    sum(form_submitted_to_blo) AS forms_submitted_to_blo,
    sum(blo_digitized) AS blo_digitized,
    today() AS report_date
FROM dim_booth_voter
GROUP BY
    booth_id, booth_name, state_id, state_name, parliament_id,
    assembly_id, cluster_id, cluster_name, unit_id, unit_name,
    constituency_id, constituency_name;

-- Verify
SELECT count() AS total_booths FROM fact_booth_sir;
