-- Destination staging tables in mytdp schema (same names as source)
-- These are needed for transforms to read from dest instead of source

USE mytdp;

CREATE TABLE IF NOT EXISTS booth (
    id VARCHAR(26) NOT NULL,
    booth_id VARCHAR(26) DEFAULT NULL,
    name VARCHAR(200) DEFAULT NULL,
    part_no VARCHAR(100) DEFAULT NULL,
    assembly_id INT DEFAULT NULL,
    parliament_id INT DEFAULT NULL,
    publication_id INT DEFAULT NULL,
    panchayat_id INT DEFAULT NULL,
    mandal_id INT DEFAULT NULL,
    town_id INT DEFAULT NULL,
    cluster_id INT DEFAULT NULL,
    unit_id INT DEFAULT NULL,
    state_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_sb_assembly (assembly_id),
    KEY idx_sb_state (state_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS assembly (
    id INT NOT NULL,
    name VARCHAR(200) DEFAULT NULL,
    parliament_id INT DEFAULT NULL,
    state_id INT DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS parliament (
    id INT NOT NULL,
    name VARCHAR(200) DEFAULT NULL,
    state_id INT DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS state (
    id INT NOT NULL,
    state_name VARCHAR(200) DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cluster (
    id INT NOT NULL,
    cluster_name VARCHAR(200) DEFAULT NULL,
    assembly_id INT DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS unit (
    id INT NOT NULL,
    unit_name VARCHAR(200) DEFAULT NULL,
    assembly_id INT DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sir_form_counts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booth_id VARCHAR(26) DEFAULT NULL,
    user_id VARCHAR(200) DEFAULT NULL,
    role_id INT DEFAULT NULL,
    forms_distributed INT DEFAULT 0,
    forms_received INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_sfc_booth (booth_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
