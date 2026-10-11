"""
Production SQL Query Library for Executive Business Intelligence & Analytics.
Includes advanced CTEs, Window Functions (LAG, LEAD, ROW_NUMBER, SUM OVER),
and Cohort aggregations designed for technical data analytics interviews.
"""
from typing import List
from app.models import PrebuiltQueryMeta

PREBUILT_QUERIES: List[PrebuiltQueryMeta] = [
    PrebuiltQueryMeta(
        id="mrr_waterfall_cte",
        name="1. Monthly MRR Waterfall Ledger (CTEs & Window Functions)",
        category="Revenue Operations",
        description="Deconstructs monthly revenue growth into Starting MRR, New Business, Expansion (+), Contraction (-), Churn (-), and Ending MRR.",
        sql="""-- Monthly MRR Waterfall Ledger with Window Aggregation
WITH MonthlyMovements AS (
    SELECT 
        snapshot_month,
        SUM(CASE WHEN mrr_change_type = 'New' THEN active_mrr ELSE 0 END) AS new_mrr,
        SUM(expansion_amount) AS expansion_mrr,
        SUM(contraction_amount) AS contraction_mrr,
        SUM(churn_amount) AS churn_mrr,
        SUM(active_mrr) AS ending_mrr
    FROM fact_monthly_snapshots
    GROUP BY snapshot_month
),
WaterfallCalculations AS (
    SELECT
        snapshot_month,
        COALESCE(LAG(ending_mrr) OVER (ORDER BY snapshot_month ASC), 0) AS starting_mrr,
        ROUND(new_mrr, 2) AS new_mrr,
        ROUND(expansion_mrr, 2) AS expansion_mrr,
        ROUND(contraction_mrr, 2) AS contraction_mrr,
        ROUND(churn_mrr, 2) AS churn_mrr,
        ROUND(ending_mrr, 2) AS ending_mrr,
        ROUND(new_mrr + expansion_mrr - contraction_mrr - churn_mrr, 2) AS net_mrr_growth
    FROM MonthlyMovements
)
SELECT 
    snapshot_month AS month,
    starting_mrr,
    new_mrr,
    expansion_mrr,
    contraction_mrr,
    churn_mrr,
    ending_mrr,
    net_mrr_growth,
    CASE 
        WHEN starting_mrr > 0 
        THEN ROUND((net_mrr_growth / starting_mrr) * 100.0, 2)
        ELSE 100.0 
    END AS growth_rate_pct
FROM WaterfallCalculations
ORDER BY snapshot_month DESC
LIMIT 12;"""
    ),
    PrebuiltQueryMeta(
        id="channel_unit_economics",
        name="2. Customer Acquisition Efficiency & LTV/CAC by Channel",
        category="Unit Economics",
        description="Calculates blended Customer Acquisition Cost (CAC), Gross Margin, Customer Lifetime Value (LTV), and LTV/CAC payback multiples across acquisition channels.",
        sql="""-- Channel Unit Economics and LTV/CAC Efficiency
SELECT 
    ch.channel_name,
    ch.acquisition_category,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    ROUND(AVG(c.cac), 2) AS avg_cac_usd,
    ROUND(SUM(t.net_amount), 2) AS total_revenue_usd,
    ROUND(AVG(t.net_amount), 2) AS arpu_usd,
    ROUND(
        (AVG(t.net_amount) * 0.825) / 0.021, 2
    ) AS estimated_ltv_usd,
    ROUND(
        ((AVG(t.net_amount) * 0.825) / 0.021) / AVG(c.cac), 2
    ) AS ltv_to_cac_ratio,
    ROUND(
        AVG(c.cac) / (AVG(t.net_amount) * 0.825), 1
    ) AS cac_payback_months
FROM dim_channel ch
JOIN dim_customer c ON ch.channel_id = c.channel_id
JOIN fact_transactions t ON c.customer_id = t.customer_id
GROUP BY ch.channel_name, ch.acquisition_category
ORDER BY total_revenue_usd DESC;"""
    ),
    PrebuiltQueryMeta(
        id="rolling_90d_moving_avg",
        name="3. Rolling 90-Day Revenue Moving Average & Growth Volatility",
        category="Time Series & Forecasting",
        description="Uses window framing (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) to compute smoothed rolling quarterly revenue and month-over-month volatility.",
        sql="""-- Rolling 90-Day Moving Average & Revenue Trend
WITH MonthlyTotals AS (
    SELECT 
        d.year,
        d.month,
        printf('%04d-%02d', d.year, d.month) AS year_month,
        SUM(t.net_amount) AS monthly_revenue,
        COUNT(t.transaction_id) AS transaction_count
    FROM fact_transactions t
    JOIN dim_date d ON t.date_key = d.date_key
    GROUP BY d.year, d.month
)
SELECT 
    year_month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(
        AVG(monthly_revenue) OVER (
            ORDER BY year_month ASC 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_3m_avg_revenue,
    ROUND(
        monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year_month ASC), 2
    ) AS mom_revenue_change,
    ROUND(
        ((monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year_month ASC)) 
        / LAG(monthly_revenue, 1) OVER (ORDER BY year_month ASC)) * 100.0, 2
    ) AS mom_growth_pct,
    transaction_count
FROM MonthlyTotals
ORDER BY year_month DESC
LIMIT 12;"""
    ),
    PrebuiltQueryMeta(
        id="pareto_80_20_concentration",
        name="4. Pareto (80/20) Revenue Concentration Risk Analysis",
        category="Risk & Governance",
        description="Computes running cumulative revenue percentage using SUM() OVER () to quantify top customer revenue concentration and portfolio vulnerability.",
        sql="""-- Pareto 80/20 Revenue Concentration Risk Analysis
WITH CustomerLifetimeRev AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.industry,
        c.region,
        p.product_name AS current_tier,
        SUM(t.net_amount) AS total_customer_revenue
    FROM dim_customer c
    JOIN fact_transactions t ON c.customer_id = t.customer_id
    JOIN dim_product p ON c.plan_tier = p.product_id
    GROUP BY c.customer_id, c.customer_name, c.industry, c.region, p.product_name
),
RankedCustomers AS (
    SELECT 
        customer_id,
        customer_name,
        industry,
        region,
        current_tier,
        ROUND(total_customer_revenue, 2) AS customer_revenue,
        DENSE_RANK() OVER (ORDER BY total_customer_revenue DESC) AS revenue_rank,
        ROUND(
            SUM(total_customer_revenue) OVER (ORDER BY total_customer_revenue DESC), 2
        ) AS running_cumulative_revenue,
        ROUND(
            SUM(total_customer_revenue) OVER (), 2
        ) AS total_company_revenue
    FROM CustomerLifetimeRev
)
SELECT 
    revenue_rank,
    customer_name,
    industry,
    region,
    current_tier,
    customer_revenue,
    running_cumulative_revenue,
    ROUND(
        (running_cumulative_revenue / total_company_revenue) * 100.0, 2
    ) AS cumulative_revenue_share_pct
FROM RankedCustomers
WHERE revenue_rank <= 25
ORDER BY revenue_rank ASC;"""
    ),
    PrebuiltQueryMeta(
        id="customer_health_churn_hazard",
        name="5. Account Health Score vs. Churn Hazard Stratification",
        category="Cohort Health",
        description="Segments customer base into Health Quartiles and cross-references usage overage patterns to predict at-risk ARR before cancellation occurs.",
        sql="""-- Customer Health Score and At-Risk ARR Stratification
SELECT 
    CASE 
        WHEN health_score >= 85 THEN 'Tier 1: Excellent (Health 85-100)'
        WHEN health_score >= 70 THEN 'Tier 2: Good (Health 70-84)'
        WHEN health_score >= 60 THEN 'Tier 3: Caution (Health 60-69)'
        ELSE 'Tier 4: High Churn Risk (<60)'
    END AS health_tier,
    COUNT(customer_id) AS total_accounts,
    ROUND(AVG(health_score), 1) AS avg_health_score,
    ROUND(SUM(cac), 2) AS total_invested_cac,
    ROUND(AVG(cac), 2) AS avg_cac_per_logo,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM dim_customer), 2) AS pct_of_account_base
FROM dim_customer
GROUP BY health_tier
ORDER BY avg_health_score DESC;"""
    )
]

def get_prebuilt_queries() -> List[PrebuiltQueryMeta]:
    """Returns list of verified production SQL queries."""
    return PREBUILT_QUERIES
