"""
Data models and response schemas for Enterprise KPI & Analytics Suite.
Fully compatible with both Pydantic v1.10 and v2.x.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExecutiveKPIs(BaseModel):
    arr: float = Field(..., description="Annual Recurring Revenue in USD")
    mrr: float = Field(..., description="Monthly Recurring Revenue in USD")
    nrr_pct: float = Field(..., description="Net Revenue Retention Percentage (e.g. 118.4%)")
    grr_pct: float = Field(..., description="Gross Revenue Retention Percentage (e.g. 93.2%)")
    active_customers: int = Field(..., description="Total active paying accounts")
    cac_payback_months: float = Field(..., description="Average CAC Payback Period in months")
    saas_quick_ratio: float = Field(..., description="SaaS Quick Ratio: (New + Expansion) / (Churn + Contraction)")
    monthly_churn_rate_pct: float = Field(..., description="Logo Churn Rate percentage")
    revenue_churn_rate_pct: float = Field(..., description="Gross Revenue Churn Rate percentage")
    arpu: float = Field(..., description="Average Revenue Per User / Account per month")
    ltv: float = Field(..., description="Estimated Customer Lifetime Value in USD")
    ltv_to_cac_ratio: float = Field(..., description="LTV / CAC efficiency multiple")
    gross_margin_pct: float = Field(..., description="Gross Margin Percentage")

class MRRWaterfallItem(BaseModel):
    month: str = Field(..., description="Month identifier (YYYY-MM)")
    starting_mrr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churn_mrr: float
    ending_mrr: float
    net_growth_mrr: float
    growth_rate_pct: float

class CohortRetentionRow(BaseModel):
    cohort_month: str = Field(..., description="Signup vintage cohort (YYYY-MM)")
    initial_accounts: int
    initial_mrr: float
    retention_rates: List[Optional[float]] = Field(..., description="List of retention percentages from M0 to M12")

class RevenueBreakdownItem(BaseModel):
    category: str
    revenue: float
    percentage: float
    customer_count: int

class RevenueBreakdowns(BaseModel):
    by_region: List[RevenueBreakdownItem]
    by_plan_tier: List[RevenueBreakdownItem]
    by_channel: List[RevenueBreakdownItem]

class SQLQueryRequest(BaseModel):
    query: str = Field(..., description="SQL SELECT query to execute against the dimensional warehouse")
    limit: Optional[int] = Field(100, description="Max rows to return (capped at 500)")

class SQLQueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    query_name: Optional[str] = None
    error: Optional[str] = None

class PrebuiltQueryMeta(BaseModel):
    id: str
    name: str
    description: str
    category: str
    sql: str

class DAXMeasureItem(BaseModel):
    id: str
    name: str
    category: str
    formula: str
    description: str
    business_impact: str

class HealthResponse(BaseModel):
    status: str
    version: str
    total_transactions: int
    total_customers: int
    months_covered: int
    warehouse_ready: bool
