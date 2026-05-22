-- models/staging/stg_stocks.sql
-- Cleans raw stocks_optimized: casts types, drops junk columns, renames

with source as (
    select * from {{ source('public', 'stocks_optimized') }}
),

cleaned as (
    select
        cast(date as date)          as date,
        ticker,
        cast(open  as numeric(12,4)) as open,
        cast(high  as numeric(12,4)) as high,
        cast(low   as numeric(12,4)) as low,
        cast(close as numeric(12,4)) as close,
        cast(volume as bigint)       as volume,
        daily_return_pct,
        ma_50,
        volatility_30d,
        volume_spike
    from source
    where ticker is not null
      and close  is not null
      and date   is not null
)

select * from cleaned
