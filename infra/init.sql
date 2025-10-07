-- Initialize Spartan Resilience Framework Database

-- Event log table for append-only provenance tracking
CREATE TABLE IF NOT EXISTS event_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    signature VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_event_log_timestamp ON event_log(timestamp);
CREATE INDEX idx_event_log_type ON event_log(event_type);

-- Business KPIs and metrics table
CREATE TABLE IF NOT EXISTS biz_kpis (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    duration_ms FLOAT,
    input_cost_usd DECIMAL(10, 5),
    output_cost_usd DECIMAL(10, 5),
    compute_cost_usd DECIMAL(10, 5),
    unit_cost_usd DECIMAL(10, 5),
    energy_joules FLOAT,
    carbon_kg FLOAT,
    carbon_intensity_g_per_kwh FLOAT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_biz_kpis_timestamp ON biz_kpis(timestamp);
CREATE INDEX idx_biz_kpis_model ON biz_kpis(model);
CREATE INDEX idx_biz_kpis_metric_type ON biz_kpis(metric_type);

-- Deployment tracking table
CREATE TABLE IF NOT EXISTS deployments (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    model VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    region VARCHAR(50),
    cost_tags JSONB,
    policy_check_passed BOOLEAN NOT NULL,
    policy_violations JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deployments_timestamp ON deployments(timestamp);
CREATE INDEX idx_deployments_model ON deployments(model);
CREATE INDEX idx_deployments_environment ON deployments(environment);

-- DORA metrics table
CREATE TABLE IF NOT EXISTS dora_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    deployment_frequency_per_day FLOAT,
    lead_time_minutes FLOAT,
    mttr_minutes FLOAT,
    change_failure_rate FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dora_metrics_timestamp ON dora_metrics(timestamp);

-- Grant permissions (adjust as needed for security)
-- GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO spartan_app;
