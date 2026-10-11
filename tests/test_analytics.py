"""
Unit and Integration Test Suite for Enterprise Executive KPI & Revenue Analytics Suite.
Verifies star schema warehouse integrity, financial waterfall balances, cohort logic,
prebuilt CTE queries, read-only security guards, and DAX catalog availability.
"""
import unittest
import sys
import os

# Insert app root into python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.warehouse import warehouse

class TestEnterpriseKPIAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fast seed for tests
        warehouse.seed_warehouse(num_customers=300, target_transactions=5000, seed=123)
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Validates /health endpoint and database readiness."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["warehouse_ready"])
        self.assertGreaterEqual(data["total_transactions"], 5000)
        self.assertEqual(data["total_customers"], 300)

    def test_02_executive_kpis(self):
        """Validates calculation of ARR, MRR, NRR, CAC payback, and SaaS Quick Ratio."""
        res = self.client.get("/api/v1/metrics/executive")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["arr"], 0)
        self.assertGreater(data["mrr"], 0)
        self.assertAlmostEqual(data["arr"], data["mrr"] * 12, delta=100.0)
        self.assertGreater(data["active_customers"], 0)
        self.assertGreater(data["nrr_pct"], 50.0)
        self.assertGreater(data["saas_quick_ratio"], 0.0)
        self.assertGreater(data["cac_payback_months"], 0.0)
        self.assertGreater(data["ltv_to_cac_ratio"], 1.0)

    def test_03_mrr_waterfall_math_balance(self):
        """Verifies that each month in the waterfall satisfies: Ending = Starting + New + Exp - Con - Churn."""
        res = self.client.get("/api/v1/metrics/mrr-waterfall")
        self.assertEqual(res.status_code, 200)
        waterfall = res.json()
        self.assertEqual(len(waterfall), 24)

        for item in waterfall:
            starting = item["starting_mrr"]
            new_m = item["new_mrr"]
            exp_m = item["expansion_mrr"]
            con_m = item["contraction_mrr"]
            chu_m = item["churn_mrr"]
            ending = item["ending_mrr"]

            computed_ending = round(starting + new_m + exp_m - con_m - chu_m, 2)
            self.assertAlmostEqual(ending, computed_ending, delta=1.0, 
                msg=f"Month {item['month']} waterfall balance mismatch: {ending} vs {computed_ending}")

    def test_04_cohort_retention_m0(self):
        """Verifies that all cohorts have 100.0% retention in Month 0."""
        res = self.client.get("/api/v1/metrics/cohorts")
        self.assertEqual(res.status_code, 200)
        cohorts = res.json()
        self.assertGreater(len(cohorts), 0)

        for c in cohorts:
            self.assertGreater(c["initial_accounts"], 0)
            self.assertGreater(c["initial_mrr"], 0.0)
            self.assertAlmostEqual(c["retention_rates"][0], 100.0, delta=0.5)

    def test_05_revenue_breakdowns(self):
        """Verifies revenue breakdown distributions across Region, Tier, and Channel."""
        res = self.client.get("/api/v1/metrics/breakdown")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        reg_pct_sum = sum(item["percentage"] for item in data["by_region"])
        self.assertAlmostEqual(reg_pct_sum, 100.0, delta=1.0)

        tier_pct_sum = sum(item["percentage"] for item in data["by_plan_tier"])
        self.assertAlmostEqual(tier_pct_sum, 100.0, delta=1.0)

        chan_pct_sum = sum(item["percentage"] for item in data["by_channel"])
        self.assertAlmostEqual(chan_pct_sum, 100.0, delta=1.0)

    def test_06_sql_query_execution_and_security_guard(self):
        """Tests SQL query sandbox execution and validates that mutations are blocked."""
        # 1. Valid SELECT query
        valid_res = self.client.post("/api/v1/analytics/query", json={
            "query": "SELECT customer_name, industry, cac FROM dim_customer ORDER BY cac DESC LIMIT 5;"
        })
        self.assertEqual(valid_res.status_code, 200)
        v_data = valid_res.json()
        self.assertIsNone(v_data.get("error"))
        self.assertEqual(len(v_data["rows"]), 5)
        self.assertIn("customer_name", v_data["columns"])
        self.assertGreater(v_data["execution_time_ms"], 0.0)

        # 2. Blocked destructive queries (Security Guardrails)
        blocked_queries = [
            "DROP TABLE dim_customer;",
            "DELETE FROM fact_transactions WHERE 1=1;",
            "UPDATE dim_customer SET cac = 0;",
            "INSERT INTO dim_product VALUES ('x', 'y', 1, 10, 'm');"
        ]
        for b_sql in blocked_queries:
            bad_res = self.client.post("/api/v1/analytics/query", json={"query": b_sql})
            self.assertEqual(bad_res.status_code, 200)
            b_data = bad_res.json()
            self.assertIsNotNone(b_data.get("error"))
            self.assertIn("prohibits", b_data["error"].lower())

    def test_07_dax_measure_catalog(self):
        """Verifies that Power BI DAX catalog returns over 20 verified formulas."""
        res = self.client.get("/api/v1/dax/catalog")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_measures"], 20)
        names = [m["name"] for m in data["measures"]]
        self.assertIn("Net Revenue", names)
        self.assertIn("Monthly Recurring Revenue (MRR)", names)
        self.assertIn("Net Revenue Retention (NRR %)", names)
        self.assertIn("SaaS Quick Ratio", names)
        self.assertIn("CAC Payback Period (Months)", names)

    def test_08_dashboard_html_render(self):
        """Verifies root endpoint GET / serves complete responsive executive dashboard."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Enterprise KPI Analytics", res.text)
        self.assertIn("Chart.js", res.text)
        self.assertIn("In-Browser SQL Query Engine", res.text)

if __name__ == "__main__":
    unittest.main()
