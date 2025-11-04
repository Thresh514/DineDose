CREATE TABLE IF NOT EXISTS drugs (
    id SERIAL PRIMARY KEY,
    product_ndc VARCHAR(50) UNIQUE,
    brand_name VARCHAR(255),
    brand_name_base VARCHAR(255),
    generic_name TEXT,
    labeler_name VARCHAR(255),
    dosage_form VARCHAR(255),
    route VARCHAR(255),
    marketing_category VARCHAR(255),
    product_type VARCHAR(255),
    application_number VARCHAR(255),
    marketing_start_date VARCHAR(20),
    listing_expiration_date VARCHAR(20),
    finished BOOLEAN
);

CREATE TABLE IF NOT EXISTS active_ingredients (
    id SERIAL PRIMARY KEY,
    drug_ndc VARCHAR(50),
    name VARCHAR(255),
    strength VARCHAR(100),
    FOREIGN KEY (drug_ndc) REFERENCES drugs(product_ndc)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS foods (
    id BIGSERIAL PRIMARY KEY,
    fdc_id BIGINT,
    description TEXT,
    fat DOUBLE PRECISION,
    carbonhydrate DOUBLE PRECISION,
    calories DOUBLE PRECISION,
    data_type VARCHAR(24),
    food_category_id VARCHAR(700),
    publication_date VARCHAR(10),
    food_category_num INT
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    role VARCHAR(50) NOT NULL DEFAULT 'patient',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(64) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
