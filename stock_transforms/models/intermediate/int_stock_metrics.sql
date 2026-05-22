-- models/intermediate/int_stock_metrics.sql
-- Adds year column and 52-week high/low per ticker per year

with stg as (
    select * from {{ ref('stg_stocks') }}
),

with_year as (
    select
        *,
        extract(year from date) as year
    from stg
),

yearly_stats as (
    select
        ticker,
        year,
        max(high)              as week52_high,
        min(low)               as week52_low,
        avg(daily_return_pct)  as avg_daily_return_pct,
        avg(volatility_30d)    as avg_volatility_30d,
        avg(volume_spike)      as avg_volume_spike,
        count(*)               as trading_days
    from with_year
    group by ticker, year
),

final as (
    select
        w.*,
        y.week52_high,
        y.week52_low,
        y.avg_daily_return_pct,
        y.avg_volatility_30d,
        y.avg_volume_spike,
        y.trading_days
    from with_year w
    left join yearly_stats y
        on w.ticker = y.ticker
        and w.year  = y.year
)

select * from final
