-- =============================================================================
-- ENTERPRISE DATA WAREHOUSE STAR SCHEMA DDL
-- Compatible with PostgreSQL, Snowflake, Amazon Redshift, and Databricks SQL
-- =============================================================================

CREATE TABLE dim_date (
    date_key            INT PRIMARY KEY,
    full_date           DATE NOT NULL,
    year                SMALLINT NOT NULL,
    quarter             SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    month_name          VARCHAR(15) NOT NULL,
    day                 SMALLINT NOT NULL,
    day_of_week         SMALLINT NOT NULL,
    day_name            VARCHAR(15) NOT NULL,
    is_weekend          BOOLEAN NOT NULL,
    fiscal_year         VARCHAR(10) NOT NULL,
    fiscal_quarter      VARCHAR(10) NOT NULL
);

CREATE TABLE dim_channel (
    channel_id           VARCHAR(32) PRIMARY KEY,
    channel_name         VARCHAR(64) NOT NULL,
    acquisition_category VARCHAR(32) NOT NULL,
    avg_conversion_rate  NUMERIC(5, 4) NOT NULL,
    cost_multiplier      NUMERIC(4, 2) NOT NULL
);

CREATE TABLE dim_product (
    product_id          VARCHAR(32) PRIMARY KEY,
    product_name        VARCHAR(64) NOT NULL,
    tier_level          SMALLINT NOT NULL,
    base_price          NUMERIC(10, 2) NOT NULL,
    billing_cycle       VARCHAR(16) NOT NULL
);

CREATE TABLE dim_customer (
    customer_id         VARCHAR(32) PRIMARY KEY,
    customer_name       VARCHAR(128) NOT NULL,
    industry            VARCHAR(64) NOT NULL,
    plan_tier           VARCHAR(32) NOT NULL REFERENCES dim_product(product_id),
    region              VARCHAR(32) NOT NULL,
    channel_id          VARCHAR(32) NOT NULL REFERENCES dim_channel(channel_id),
    signup_date         DATE NOT NULL,
    cac                 NUMERIC(10, 2) NOT NULL,
    health_score        NUMERIC(4, 1) NOT NULL,
    status              VARCHAR(16) NOT NULL
);

CREATE TABLE fact_transactions (
    transaction_id      VARCHAR(32) PRIMARY KEY,
    date_key            INT NOT NULL REFERENCES dim_date(date_key),
    customer_id         VARCHAR(32) NOT NULL REFERENCES dim_customer(customer_id),
    product_id          VARCHAR(32) NOT NULL REFERENCES dim_product(product_id),
    channel_id          VARCHAR(32) NOT NULL REFERENCES dim_channel(channel_id),
    event_type          VARCHAR(32) NOT NULL,
    gross_amount        NUMERIC(12, 2) NOT NULL,
    discount_amount     NUMERIC(12, 2) NOT NULL,
    refund_amount       NUMERIC(12, 2) NOT NULL,
    net_amount          NUMERIC(12, 2) NOT NULL,
    payment_status      VARCHAR(16) NOT NULL,
    currency            VARCHAR(3) NOT NULL
);

CREATE TABLE fact_monthly_snapshots (
    id                  BIGSERIAL PRIMARY KEY,
    snapshot_month      VARCHAR(7) NOT NULL,
    customer_id         VARCHAR(32) NOT NULL REFERENCES dim_customer(customer_id),
    plan_tier           VARCHAR(32) NOT NULL REFERENCES dim_product(product_id),
    active_mrr          NUMERIC(12, 2) NOT NULL,
    mrr_change_type     VARCHAR(16) NOT NULL,
    expansion_amount    NUMERIC(12, 2) NOT NULL,
    contraction_amount  NUMERIC(12, 2) NOT NULL,
    churn_amount        NUMERIC(12, 2) NOT NULL,
    net_mrr             NUMERIC(12, 2) NOT NULL
);

-- Performance Analytics Indexes
CREATE INDEX idx_fact_tx_date ON fact_transactions(date_key);
CREATE INDEX idx_fact_tx_cust ON fact_transactions(customer_id);
CREATE INDEX idx_fact_tx_type ON fact_transactions(event_type);
CREATE INDEX idx_fact_snap_month ON fact_monthly_snapshots(snapshot_month);
CREATE INDEX idx_fact_snap_cust ON fact_monthly_snapshots(customer_id);
