-- Migration: Create sync_config and sync_status tables
-- Run this on the destination database

-- Config table: stores which tables to sync and how
CREATE TABLE IF NOT EXISTS sync_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    dest_table VARCHAR(100) NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    poll_interval INT DEFAULT 30,
    batch_size INT DEFAULT 500,
    watermark_column VARCHAR(100) DEFAULT 'updated_at',
    primary_key VARCHAR(100) DEFAULT 'id',
    columns_json TEXT,
    filters_json TEXT,
    timezone_offset INT DEFAULT 0,
    last_synced_at DATETIME DEFAULT NULL,
    last_record_id VARCHAR(100) DEFAULT NULL,
    inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Status table: tracks runtime sync status per table
CREATE TABLE IF NOT EXISTS sync_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    status ENUM('running','idle','error','disabled') DEFAULT 'idle',
    last_sync_at DATETIME DEFAULT NULL,
    last_sync_duration_ms INT DEFAULT NULL,
    last_sync_rows INT DEFAULT NULL,
    last_error TEXT DEFAULT NULL,
    last_error_at DATETIME DEFAULT NULL,
    consecutive_errors INT DEFAULT 0,
    total_rows_synced BIGINT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- History table: last 10 sync runs per table
CREATE TABLE IF NOT EXISTS sync_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    status ENUM('success','error') NOT NULL,
    rows_synced INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    error_message TEXT DEFAULT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_history_table (table_name, completed_at DESC)
);
