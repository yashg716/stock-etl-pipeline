-- Create a partitioned version of the table
CREATE TABLE stocks_partitioned (
    date        DATE        NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    volume      DOUBLE PRECISION,
    ticker      VARCHAR(10),
    adj_close   DOUBLE PRECISION
) PARTITION BY RANGE (date);

-- Create one partition per year
CREATE TABLE stocks_part_2019 PARTITION OF stocks_partitioned FOR VALUES FROM ('2019-01-01') TO ('2020-01-01');
CREATE TABLE stocks_part_2020 PARTITION OF stocks_partitioned FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE stocks_part_2021 PARTITION OF stocks_partitioned FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE stocks_part_2022 PARTITION OF stocks_partitioned FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE stocks_part_2023 PARTITION OF stocks_partitioned FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE stocks_part_2024 PARTITION OF stocks_partitioned FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Copy data from optimized table
INSERT INTO stocks_partitioned SELECT * FROM stocks_optimized;

-- Drop the old B-tree date index
DROP INDEX IF EXISTS idx_date;

-- Replace with BRIN — tiny footprint, perfect for sequential date data
CREATE INDEX idx_date_brin ON stocks_optimized USING BRIN (date);


-- Check current table size
SELECT pg_size_pretty(pg_total_relation_size('stocks_optimized'));

-- Optimal column order: DOUBLE PRECISION (8 bytes) first, VARCHAR last
-- You'd rebuild the table with columns in this order:
-- open, high, low, close, adj_close, volume → date → ticker


-- Reclaim dead space and update query planner statistics
VACUUM ANALYZE stocks_optimized;
VACUUM ANALYZE stocks_partitioned;

-- Check actual table size after vacuum
SELECT 
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
WHERE relname LIKE 'stocks%'
ORDER BY pg_total_relation_size(relid) DESC;

ALTER TABLE stocks_optimized
ADD COLUMN IF NOT EXISTS daily_return_pct  DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS ma_50             DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS volatility_30d    DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS volume_spike      DOUBLE PRECISION;



SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'stocks_optimized'
ORDER BY ordinal_position;