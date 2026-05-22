-- models/marts/mart_stock_summary.sql
-- Final analysis-ready table: one row per ticker per year
-- Answers: which stocks had best risk-adjusted returns?

with int_data as (
    select * from {{ ref('int_stock_metrics') }}
),

summary as (
    select
        ticker,
        year,
        round(cast(avg_daily_return_pct as numeric), 4)  as avg_daily_return_pct,
        round(cast(avg_volatility_30d   as numeric), 4)  as avg_volatility_30d,
        round(cast(avg_volume_spike     as numeric), 4)  as avg_volume_spike,
        round(cast(week52_high          as numeric), 2)  as week52_high,
        round(cast(week52_low           as numeric), 2)  as week52_low,
        trading_days,

        -- Sharpe-style ratio: return per unit of risk
        round(
            cast(avg_daily_return_pct as numeric) /
            nullif(cast(avg_volatility_30d as numeric), 0),
        6) as return_per_risk

    from int_data
    group by
        ticker, year,
        avg_daily_return_pct, avg_volatility_30d,
        avg_volume_spike, week52_high, week52_low,
        trading_days
)

select * from summary
order by year desc, return_per_risk desc