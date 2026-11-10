CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    activity_date DATE NOT NULL,
    notes TEXT,
    calculated_emissions_kg FLOAT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activities_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS emission_factors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    emission_factor FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    source VARCHAR(255) NOT NULL,
    reference_year INT NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    source_url VARCHAR(500),
    geography VARCHAR(100),
    gas_basis VARCHAR(20),
    methodology VARCHAR(100),
    verification_status VARCHAR(50),
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emission_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    co2e_kg FLOAT NOT NULL,
    recorded_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_emission_records_activity FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    monthly_target_kg FLOAT NOT NULL,
    start_month VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
