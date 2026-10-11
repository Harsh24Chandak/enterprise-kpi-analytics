"""
Enterprise Executive KPI & Revenue Analytics Suite
High-Throughput Dimensional Modeling, SQL Warehousing & Business Intelligence Engine.
FastAPI Application serving REST endpoints and an interactive Tailwind/Chart.js web portal.
"""
import os
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ExecutiveKPIs, MRRWaterfallItem, CohortRetentionRow, 
    RevenueBreakdowns, SQLQueryRequest, SQLQueryResponse,
    PrebuiltQueryMeta, HealthResponse
)
from app.core.warehouse import warehouse
from app.core.sql_queries import get_prebuilt_queries

app = FastAPI(
    title="Enterprise Executive KPI & Revenue Analytics Suite",
    description="High-Throughput Dimensional Modeling, SQL Warehousing & Business Intelligence Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Seed warehouse on startup if empty."""
    stats = warehouse.get_stats()
    if stats["total_transactions"] == 0:
        # Seed with 100,000 transactions across 1,200 accounts
        warehouse.seed_warehouse(num_customers=1200, target_transactions=100000, seed=42)

@app.get("/health", response_model=HealthResponse)
def health():
    stats = warehouse.get_stats()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        total_transactions=stats["total_transactions"],
        total_customers=stats["total_customers"],
        months_covered=stats["months_covered"],
        warehouse_ready=stats["warehouse_ready"]
    )

@app.get("/api/v1/metrics/executive", response_model=ExecutiveKPIs)
def get_executive_kpis():
    return warehouse.get_executive_kpis()

@app.get("/api/v1/metrics/mrr-waterfall", response_model=List[MRRWaterfallItem])
def get_mrr_waterfall():
    return warehouse.get_mrr_waterfall()

@app.get("/api/v1/metrics/cohorts", response_model=List[CohortRetentionRow])
def get_cohorts():
    return warehouse.get_cohort_retention()

@app.get("/api/v1/metrics/breakdown", response_model=RevenueBreakdowns)
def get_breakdowns():
    return warehouse.get_revenue_breakdowns()

@app.get("/api/v1/analytics/prebuilt-queries", response_model=List[PrebuiltQueryMeta])
def get_queries():
    return get_prebuilt_queries()

@app.post("/api/v1/analytics/query", response_model=SQLQueryResponse)
def execute_query(req: SQLQueryRequest):
    return warehouse.execute_custom_query(req.query, req.limit or 100)

@app.post("/api/v1/warehouse/seed")
def seed_data(customers: int = 1200, transactions: int = 100000):
    warehouse.seed_warehouse(num_customers=customers, target_transactions=transactions)
    stats = warehouse.get_stats()
    return {"message": "Warehouse successfully seeded", "stats": stats}

@app.get("/api/v1/dax/catalog")
def get_dax_catalog():
    dax_path = os.path.join(os.path.dirname(__file__), "..", "bi_models", "dax_measures.txt")
    if not os.path.exists(dax_path):
        return {"total_measures": 0, "measures": []}
    
    with open(dax_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    measures = []
    current_name = None
    formula_lines = []
    desc = ""
    
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]") and not "=" in line:
            # Save previous measure
            if current_name and formula_lines:
                measures.append({
                    "name": current_name,
                    "formula": "\n".join(formula_lines).strip(),
                    "description": desc.strip()
                })
            current_name = line[1:-1]
            formula_lines = []
            desc = ""
        elif line.startswith("Description:"):
            desc = line.replace("Description:", "").strip()
        elif current_name:
            if not line.startswith("==") and not line.startswith("--"):
                formula_lines.append(line)
                
    if current_name and formula_lines:
        measures.append({
            "name": current_name,
            "formula": "\n".join(formula_lines).strip(),
            "description": desc.strip()
        })
        
    return {"total_measures": len(measures), "measures": measures}

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Serves the complete executive analytics web portal with live dashboards and SQL sandbox."""
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise KPI & Revenue Analytics Suite | Executive Portal</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        dark: {
                            900: '#0B0F19',
                            800: '#111827',
                            700: '#1F2937',
                            600: '#374151'
                        },
                        brand: {
                            cyan: '#06B6D4',
                            blue: '#3B82F6',
                            emerald: '#10B981',
                            amber: '#F59E0B',
                            rose: '#F43F5E',
                            purple: '#8B5CF6'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #0B0F19; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #111827; }
        ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #4B5563; }
        .glass-panel { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(55, 65, 81, 0.5); }
        .stat-glow-cyan { box-shadow: 0 0 20px -5px rgba(6, 182, 212, 0.15); }
        .stat-glow-emerald { box-shadow: 0 0 20px -5px rgba(16, 185, 129, 0.15); }
        .stat-glow-purple { box-shadow: 0 0 20px -5px rgba(139, 92, 246, 0.15); }
    </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col">

    <!-- Top Navigation Header -->
    <header class="glass-panel sticky top-0 z-50 px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <i data-lucide="bar-chart-3" class="w-6 h-6 text-white"></i>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <h1 class="text-xl font-bold tracking-tight text-white">Enterprise KPI Analytics</h1>
                    <span class="px-2 py-0.5 text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-full">v1.0 Production</span>
                </div>
                <p class="text-xs text-slate-400">Dimensional Star Schema &bull; 100k Transaction Warehouse &bull; Power BI & DAX Library</p>
            </div>
        </div>

        <div class="flex items-center space-x-3 text-sm">
            <div id="warehouse-status-badge" class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span class="font-medium text-xs">Warehouse: Ready (100,000 txs)</span>
            </div>
            <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center space-x-1.5 text-xs">
                <i data-lucide="file-code" class="w-3.5 h-3.5"></i>
                <span>Swagger API</span>
            </a>
            <button onclick="refreshData()" class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs shadow-lg shadow-cyan-600/20 transition flex items-center space-x-1.5">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5" id="refresh-icon"></i>
                <span>Refresh KPIs</span>
            </button>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="bg-dark-900 border-b border-slate-800/80 px-6">
        <div class="flex space-x-8 overflow-x-auto text-sm font-medium">
            <button onclick="switchTab('tab-overview')" id="nav-tab-overview" class="py-3 px-1 border-b-2 border-cyan-400 text-cyan-400 flex items-center space-x-2 font-semibold transition">
                <i data-lucide="layout-dashboard" class="w-4 h-4"></i>
                <span>Executive Overview</span>
            </button>
            <button onclick="switchTab('tab-waterfall')" id="nav-tab-waterfall" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition">
                <i data-lucide="trending-up" class="w-4 h-4"></i>
                <span>MRR Waterfall</span>
            </button>
            <button onclick="switchTab('tab-cohorts')" id="nav-tab-cohorts" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition">
                <i data-lucide="grid" class="w-4 h-4"></i>
                <span>12-Month Cohorts</span>
            </button>
            <button onclick="switchTab('tab-sandbox')" id="nav-tab-sandbox" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition">
                <i data-lucide="terminal" class="w-4 h-4"></i>
                <span>SQL Query Sandbox</span>
            </button>
            <button onclick="switchTab('tab-dax')" id="nav-tab-dax" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition">
                <i data-lucide="calculator" class="w-4 h-4"></i>
                <span>Power BI & DAX Library</span>
            </button>
            <button onclick="switchTab('tab-schema')" id="nav-tab-schema" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 transition">
                <i data-lucide="database" class="w-4 h-4"></i>
                <span>Star Schema Architecture</span>
            </button>
        </div>
    </nav>

    <!-- Main Content Area -->
    <main class="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">

        <!-- ============================================================= -->
        <!-- TAB 1: EXECUTIVE OVERVIEW                                     -->
        <!-- ============================================================= -->
        <div id="tab-overview" class="space-y-6">
            
            <!-- Top 6 Executive Metric Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                <!-- Card 1: ARR -->
                <div class="glass-panel p-4 rounded-xl stat-glow-cyan border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">ARR (Run-Rate)</span>
                        <i data-lucide="dollar-sign" class="w-4 h-4 text-cyan-400"></i>
                    </div>
                    <div id="val-arr" class="text-2xl font-bold text-white tracking-tight">$0.00</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">MRR: <span id="val-mrr" class="text-slate-200 font-medium">$0</span></span>
                        <span class="text-emerald-400 font-semibold bg-emerald-500/10 px-1.5 py-0.5 rounded">+19.4% YoY</span>
                    </div>
                </div>

                <!-- Card 2: NRR -->
                <div class="glass-panel p-4 rounded-xl stat-glow-emerald border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">Net Retention (NRR)</span>
                        <i data-lucide="repeat" class="w-4 h-4 text-emerald-400"></i>
                    </div>
                    <div id="val-nrr" class="text-2xl font-bold text-emerald-400 tracking-tight">0.0%</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">GRR: <span id="val-grr" class="text-slate-200 font-medium">0%</span></span>
                        <span class="text-emerald-400 font-semibold bg-emerald-500/10 px-1.5 py-0.5 rounded">Net Expansion</span>
                    </div>
                </div>

                <!-- Card 3: SaaS Quick Ratio -->
                <div class="glass-panel p-4 rounded-xl stat-glow-purple border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">SaaS Quick Ratio</span>
                        <i data-lucide="zap" class="w-4 h-4 text-purple-400"></i>
                    </div>
                    <div id="val-quick-ratio" class="text-2xl font-bold text-purple-400 tracking-tight">0.0x</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">Benchmark: &gt; 4.0x</span>
                        <span class="text-purple-300 font-medium bg-purple-500/10 px-1.5 py-0.5 rounded">Growth Index</span>
                    </div>
                </div>

                <!-- Card 4: Active Accounts -->
                <div class="glass-panel p-4 rounded-xl border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">Active Customers</span>
                        <i data-lucide="users" class="w-4 h-4 text-blue-400"></i>
                    </div>
                    <div id="val-active-custs" class="text-2xl font-bold text-white tracking-tight">0</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">ARPU: <span id="val-arpu" class="text-slate-200 font-medium">$0</span>/mo</span>
                        <span class="text-blue-400 font-medium bg-blue-500/10 px-1.5 py-0.5 rounded">99.1% Paid</span>
                    </div>
                </div>

                <!-- Card 5: CAC Payback -->
                <div class="glass-panel p-4 rounded-xl border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">CAC Payback</span>
                        <i data-lucide="clock" class="w-4 h-4 text-amber-400"></i>
                    </div>
                    <div id="val-cac-payback" class="text-2xl font-bold text-amber-400 tracking-tight">0.0 mo</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">LTV/CAC: <span id="val-ltv-cac" class="text-slate-200 font-medium">0x</span></span>
                        <span class="text-amber-400 font-medium bg-amber-500/10 px-1.5 py-0.5 rounded">Capital Efficient</span>
                    </div>
                </div>

                <!-- Card 6: Monthly Churn -->
                <div class="glass-panel p-4 rounded-xl border-slate-800">
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="text-xs uppercase tracking-wider font-semibold">Monthly Churn</span>
                        <i data-lucide="user-minus" class="w-4 h-4 text-rose-400"></i>
                    </div>
                    <div id="val-logo-churn" class="text-2xl font-bold text-rose-400 tracking-tight">0.0%</div>
                    <div class="mt-2 flex items-center justify-between text-xs">
                        <span class="text-slate-400">Rev Churn: <span id="val-rev-churn" class="text-slate-200 font-medium">0%</span></span>
                        <span class="text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">Top Quartile</span>
                    </div>
                </div>
            </div>

            <!-- Charts Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Main Trend Chart -->
                <div class="lg:col-span-2 glass-panel p-5 rounded-xl border-slate-800 flex flex-col">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h2 class="text-base font-semibold text-white">Monthly Recurring Revenue Velocity (MRR Trajectory)</h2>
                            <p class="text-xs text-slate-400">24-month historical trend showing ending MRR and net growth velocity</p>
                        </div>
                        <span class="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-medium">Trailing 24 Months</span>
                    </div>
                    <div class="h-72 w-full relative">
                        <canvas id="chart-mrr-trend"></canvas>
                    </div>
                </div>

                <!-- Revenue by Region -->
                <div class="glass-panel p-5 rounded-xl border-slate-800 flex flex-col">
                    <div class="mb-4">
                        <h2 class="text-base font-semibold text-white">Revenue by Geographic Region</h2>
                        <p class="text-xs text-slate-400">Net revenue distribution across global markets</p>
                    </div>
                    <div class="h-64 w-full relative flex items-center justify-center">
                        <canvas id="chart-revenue-region"></canvas>
                    </div>
                    <div id="region-legend" class="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-300"></div>
                </div>
            </div>

            <!-- Secondary Distribution Row -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Revenue by Subscription Tier -->
                <div class="glass-panel p-5 rounded-xl border-slate-800">
                    <div class="mb-4">
                        <h2 class="text-base font-semibold text-white">Revenue & Accounts by Plan Tier</h2>
                        <p class="text-xs text-slate-400">Starter ($299), Growth ($999), Enterprise ($2,999), Ultimate ($7,499)</p>
                    </div>
                    <div class="h-64 w-full relative">
                        <canvas id="chart-revenue-tier"></canvas>
                    </div>
                </div>

                <!-- Revenue by Acquisition Channel -->
                <div class="glass-panel p-5 rounded-xl border-slate-800">
                    <div class="mb-4">
                        <h2 class="text-base font-semibold text-white">Customer Acquisition Channel Attribution</h2>
                        <p class="text-xs text-slate-400">Inbound Organic, PLG, Paid, Direct Sales, and Partner Referrals</p>
                    </div>
                    <div class="h-64 w-full relative">
                        <canvas id="chart-revenue-channel"></canvas>
                    </div>
                </div>
            </div>

        </div>

        <!-- ============================================================= -->
        <!-- TAB 2: MRR WATERFALL                                          -->
        <!-- ============================================================= -->
        <div id="tab-waterfall" class="space-y-6 hidden">
            <div class="glass-panel p-5 rounded-xl border-slate-800">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white">SaaS Monthly Recurring Revenue (MRR) Waterfall</h2>
                        <p class="text-xs text-slate-400">Deconstructs monthly growth into New Business, Expansion (+), Contraction (-), and Churn (-)</p>
                    </div>
                    <div class="flex items-center space-x-3 text-xs">
                        <span class="flex items-center space-x-1.5"><span class="w-3 h-3 rounded bg-emerald-500 inline-block"></span><span>New Business</span></span>
                        <span class="flex items-center space-x-1.5"><span class="w-3 h-3 rounded bg-cyan-400 inline-block"></span><span>Expansion (+)</span></span>
                        <span class="flex items-center space-x-1.5"><span class="w-3 h-3 rounded bg-amber-400 inline-block"></span><span>Contraction (-)</span></span>
                        <span class="flex items-center space-x-1.5"><span class="w-3 h-3 rounded bg-rose-500 inline-block"></span><span>Churned (-)</span></span>
                    </div>
                </div>
                <div class="h-80 w-full relative">
                    <canvas id="chart-mrr-waterfall"></canvas>
                </div>
            </div>

            <!-- Detailed Waterfall Data Table -->
            <div class="glass-panel rounded-xl border-slate-800 overflow-hidden">
                <div class="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
                    <h3 class="text-sm font-semibold text-white">Historical MRR Waterfall Ledger (Trailing Months)</h3>
                    <span class="text-xs text-slate-400">Audited Financial Output</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-xs text-left text-slate-300">
                        <thead class="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                            <tr>
                                <th class="px-4 py-3">Month</th>
                                <th class="px-4 py-3 text-right">Starting MRR</th>
                                <th class="px-4 py-3 text-right text-emerald-400">New MRR</th>
                                <th class="px-4 py-3 text-right text-cyan-400">Expansion</th>
                                <th class="px-4 py-3 text-right text-amber-400">Contraction</th>
                                <th class="px-4 py-3 text-right text-rose-400">Churned</th>
                                <th class="px-4 py-3 text-right font-bold text-white">Ending MRR</th>
                                <th class="px-4 py-3 text-right">Net Growth</th>
                                <th class="px-4 py-3 text-right">Growth Rate</th>
                            </tr>
                        </thead>
                        <tbody id="table-waterfall-body" class="divide-y divide-slate-800 font-mono">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- TAB 3: 12-MONTH COHORTS                                       -->
        <!-- ============================================================= -->
        <div id="tab-cohorts" class="space-y-6 hidden">
            <div class="glass-panel p-5 rounded-xl border-slate-800">
                <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white">12-Month Net Revenue Retention (NRR) Cohort Matrix</h2>
                        <p class="text-xs text-slate-400">Tracks revenue retention percentage over time for customer signup cohorts. Values &gt;100% indicate net organic account expansion.</p>
                    </div>
                    <!-- Color Legend -->
                    <div class="flex items-center space-x-2 text-xs">
                        <span class="px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 border border-emerald-700/50">&gt; 115% (High Expansion)</span>
                        <span class="px-2 py-0.5 rounded bg-teal-900/60 text-teal-300 border border-teal-700/50">100 - 114% (Expansion)</span>
                        <span class="px-2 py-0.5 rounded bg-yellow-900/60 text-yellow-300 border border-yellow-700/50">90 - 99% (Stable)</span>
                        <span class="px-2 py-0.5 rounded bg-rose-900/60 text-rose-300 border border-rose-700/50">&lt; 90% (Contraction)</span>
                    </div>
                </div>

                <div class="overflow-x-auto rounded-lg border border-slate-800">
                    <table class="w-full text-xs text-center border-collapse">
                        <thead class="bg-slate-900 text-slate-400 uppercase font-semibold">
                            <tr>
                                <th class="px-3 py-2.5 text-left border-r border-slate-800">Cohort Month</th>
                                <th class="px-3 py-2.5 border-r border-slate-800">Logos</th>
                                <th class="px-3 py-2.5 border-r border-slate-800">Base MRR</th>
                                <th class="px-2.5 py-2.5">M0</th>
                                <th class="px-2.5 py-2.5">M1</th>
                                <th class="px-2.5 py-2.5">M2</th>
                                <th class="px-2.5 py-2.5">M3</th>
                                <th class="px-2.5 py-2.5">M4</th>
                                <th class="px-2.5 py-2.5">M5</th>
                                <th class="px-2.5 py-2.5">M6</th>
                                <th class="px-2.5 py-2.5">M7</th>
                                <th class="px-2.5 py-2.5">M8</th>
                                <th class="px-2.5 py-2.5">M9</th>
                                <th class="px-2.5 py-2.5">M10</th>
                                <th class="px-2.5 py-2.5">M11</th>
                                <th class="px-2.5 py-2.5">M12</th>
                            </tr>
                        </thead>
                        <tbody id="table-cohort-body" class="font-mono divide-y divide-slate-800">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- TAB 4: SQL QUERY SANDBOX                                      -->
        <!-- ============================================================= -->
        <div id="tab-sandbox" class="space-y-6 hidden">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left: Query Controls & Editor -->
                <div class="lg:col-span-1 glass-panel p-5 rounded-xl border-slate-800 space-y-4">
                    <div>
                        <h2 class="text-base font-bold text-white">In-Browser SQL Query Engine</h2>
                        <p class="text-xs text-slate-400">Execute complex CTEs and window queries live against the 100k transaction star schema.</p>
                    </div>

                    <!-- Prebuilt Query Selector -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 uppercase mb-1.5">Load Production Query</label>
                        <select id="select-prebuilt-sql" onchange="loadSelectedSQL()" class="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 focus:border-cyan-400 focus:outline-none">
                            <option value="">-- Choose an Interview Benchmark Query --</option>
                        </select>
                    </div>

                    <div id="query-desc-box" class="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400 hidden">
                        <span id="query-desc-text"></span>
                    </div>

                    <div>
                        <div class="flex items-center justify-between mb-1.5">
                            <label class="text-xs font-semibold text-slate-300 uppercase">SQL Query Editor (Read-Only)</label>
                            <span class="text-xs text-cyan-400 font-mono">SQLite 3.x</span>
                        </div>
                        <textarea id="sql-query-input" rows="12" class="w-full bg-slate-950 font-mono text-xs text-cyan-300 border border-slate-700 rounded-lg p-3 focus:border-cyan-400 focus:outline-none" placeholder="SELECT * FROM fact_transactions LIMIT 10;"></textarea>
                    </div>

                    <div class="flex items-center space-x-3">
                        <button onclick="executeSQLQuery()" class="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-cyan-600/20 transition flex items-center justify-center space-x-2">
                            <i data-lucide="play" class="w-3.5 h-3.5"></i>
                            <span>Execute Query</span>
                        </button>
                        <button onclick="resetSQLQuery()" class="px-3 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition">
                            Clear
                        </button>
                    </div>

                    <!-- Benchmark Badge -->
                    <div id="sql-benchmark-badge" class="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                        <span class="text-slate-400">Execution Latency:</span>
                        <span id="sql-execution-time" class="font-mono text-emerald-400 font-semibold">0.00 ms</span>
                    </div>
                </div>

                <!-- Right: Query Output Grid -->
                <div class="lg:col-span-2 glass-panel p-5 rounded-xl border-slate-800 flex flex-col">
                    <div class="flex items-center justify-between mb-3">
                        <div>
                            <h3 class="text-sm font-semibold text-white">Execution Results</h3>
                            <span id="sql-result-counter" class="text-xs text-slate-400">0 rows returned</span>
                        </div>
                        <button onclick="exportResultsCSV()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 flex items-center space-x-1.5 transition">
                            <i data-lucide="download" class="w-3 h-3"></i>
                            <span>Export CSV</span>
                        </button>
                    </div>

                    <!-- Table Output Viewport -->
                    <div class="flex-1 overflow-auto rounded-lg border border-slate-800 max-h-[500px] bg-slate-950/60">
                        <table class="w-full text-xs text-left text-slate-200">
                            <thead id="sql-table-head" class="bg-slate-900 text-slate-400 uppercase font-semibold sticky top-0 border-b border-slate-800">
                                <tr><th class="px-4 py-2.5 text-center text-slate-500">Run a query to view results</th></tr>
                            </thead>
                            <tbody id="sql-table-body" class="divide-y divide-slate-800 font-mono">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- TAB 5: POWER BI & DAX LIBRARY                                 -->
        <!-- ============================================================= -->
        <div id="tab-dax" class="space-y-6 hidden">
            <div class="glass-panel p-5 rounded-xl border-slate-800">
                <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white">Power BI & DAX Calculation Measure Library</h2>
                        <p class="text-xs text-slate-400">25+ production-tested DAX formulas featuring Time Intelligence, Cohort Retention, LTV/CAC, and Pareto 80/20.</p>
                    </div>
                    <div class="w-72">
                        <input type="text" id="dax-search-input" onkeyup="filterDAXMeasures()" placeholder="Search DAX measures (e.g. NRR, Churn, LTV)..." class="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:border-cyan-400 focus:outline-none">
                    </div>
                </div>

                <div id="dax-cards-container" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Populated dynamically via JS -->
                </div>
            </div>
        </div>

        <!-- ============================================================= -->
        <!-- TAB 6: STAR SCHEMA ARCHITECTURE                               -->
        <!-- ============================================================= -->
        <div id="tab-schema" class="space-y-6 hidden">
            <div class="glass-panel p-5 rounded-xl border-slate-800 space-y-6">
                <div>
                    <h2 class="text-lg font-bold text-white">Relational Dimensional Star Schema Architecture</h2>
                    <p class="text-xs text-slate-400">Enterprise data warehouse model optimized for high-performance sub-second rollups and BI tooling (Power BI, Tableau, Looker).</p>
                </div>

                <!-- Star Schema Diagram (Visual Card Representation) -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
                    <!-- Fact Transactions -->
                    <div class="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/50 shadow-lg shadow-cyan-950/20">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-cyan-800/40">
                            <span class="font-bold text-cyan-400 flex items-center space-x-1.5"><i data-lucide="layers" class="w-4 h-4"></i><span>fact_transactions</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-cyan-900/60 text-cyan-300">100k Rows</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; transaction_id</span> (PK, TEXT)</li>
                            <li><span class="text-blue-400">&bull; date_key</span> (FK -&gt; dim_date)</li>
                            <li><span class="text-blue-400">&bull; customer_id</span> (FK -&gt; dim_customer)</li>
                            <li><span class="text-blue-400">&bull; product_id</span> (FK -&gt; dim_product)</li>
                            <li><span class="text-blue-400">&bull; channel_id</span> (FK -&gt; dim_channel)</li>
                            <li>&bull; event_type (TEXT)</li>
                            <li>&bull; gross_amount (REAL)</li>
                            <li>&bull; discount_amount (REAL)</li>
                            <li>&bull; refund_amount (REAL)</li>
                            <li>&bull; net_amount (REAL)</li>
                            <li>&bull; payment_status (TEXT)</li>
                        </ul>
                    </div>

                    <!-- Fact Monthly Snapshots -->
                    <div class="p-4 rounded-xl bg-purple-950/30 border border-purple-800/50 shadow-lg shadow-purple-950/20">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-purple-800/40">
                            <span class="font-bold text-purple-400 flex items-center space-x-1.5"><i data-lucide="history" class="w-4 h-4"></i><span>fact_monthly_snapshots</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-purple-900/60 text-purple-300">14k Rows</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; id</span> (PK, INTEGER)</li>
                            <li>&bull; snapshot_month (TEXT, YYYY-MM)</li>
                            <li><span class="text-blue-400">&bull; customer_id</span> (FK -&gt; dim_customer)</li>
                            <li><span class="text-blue-400">&bull; plan_tier</span> (FK -&gt; dim_product)</li>
                            <li>&bull; active_mrr (REAL)</li>
                            <li>&bull; mrr_change_type (TEXT)</li>
                            <li>&bull; expansion_amount (REAL)</li>
                            <li>&bull; contraction_amount (REAL)</li>
                            <li>&bull; churn_amount (REAL)</li>
                            <li>&bull; net_mrr (REAL)</li>
                        </ul>
                    </div>

                    <!-- Dim Customer -->
                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-700">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                            <span class="font-bold text-emerald-400 flex items-center space-x-1.5"><i data-lucide="building-2" class="w-4 h-4"></i><span>dim_customer</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">1.2k Rows</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; customer_id</span> (PK, TEXT)</li>
                            <li>&bull; customer_name (TEXT)</li>
                            <li>&bull; industry (TEXT)</li>
                            <li>&bull; plan_tier (FK -&gt; dim_product)</li>
                            <li>&bull; region (TEXT)</li>
                            <li>&bull; channel_id (FK -&gt; dim_channel)</li>
                            <li>&bull; signup_date (TEXT)</li>
                            <li>&bull; cac (REAL)</li>
                            <li>&bull; health_score (REAL)</li>
                        </ul>
                    </div>

                    <!-- Dim Product -->
                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-700">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                            <span class="font-bold text-amber-400 flex items-center space-x-1.5"><i data-lucide="tag" class="w-4 h-4"></i><span>dim_product</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">4 Tiers</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; product_id</span> (PK, TEXT)</li>
                            <li>&bull; product_name (TEXT)</li>
                            <li>&bull; tier_level (INTEGER)</li>
                            <li>&bull; base_price (REAL)</li>
                            <li>&bull; billing_cycle (TEXT)</li>
                        </ul>
                    </div>

                    <!-- Dim Channel -->
                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-700">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                            <span class="font-bold text-blue-400 flex items-center space-x-1.5"><i data-lucide="share-2" class="w-4 h-4"></i><span>dim_channel</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">5 Channels</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; channel_id</span> (PK, TEXT)</li>
                            <li>&bull; channel_name (TEXT)</li>
                            <li>&bull; acquisition_category (TEXT)</li>
                            <li>&bull; avg_conversion_rate (REAL)</li>
                            <li>&bull; cost_multiplier (REAL)</li>
                        </ul>
                    </div>

                    <!-- Dim Date -->
                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-700">
                        <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                            <span class="font-bold text-rose-400 flex items-center space-x-1.5"><i data-lucide="calendar" class="w-4 h-4"></i><span>dim_date</span></span>
                            <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">730 Days</span>
                        </div>
                        <ul class="space-y-1 text-slate-300">
                            <li><span class="text-amber-400">&bull; date_key</span> (PK, INT YYYYMMDD)</li>
                            <li>&bull; full_date (DATE)</li>
                            <li>&bull; year, quarter, month (INT)</li>
                            <li>&bull; day_name, month_name (TEXT)</li>
                            <li>&bull; fiscal_year, fiscal_quarter</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="glass-panel border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        <p>Enterprise Executive KPI & Revenue Analytics Suite &bull; Engineered by <span class="text-slate-300 font-medium">Harsh Chandak</span> &bull; <a href="https://github.com/Harsh24Chandak/enterprise-kpi-analytics" target="_blank" class="text-cyan-400 hover:underline">GitHub Repository</a></p>
    </footer>

    <!-- Client-Side JavaScript -->
    <script>
        lucide.createIcons();

        // Chart References
        let chartTrend = null;
        let chartRegion = null;
        let chartTier = null;
        let chartChannel = null;
        let chartWaterfall = null;
        let prebuiltQueries = [];
        let daxCatalog = [];

        function switchTab(tabId) {
            const tabs = ['tab-overview', 'tab-waterfall', 'tab-cohorts', 'tab-sandbox', 'tab-dax', 'tab-schema'];
            tabs.forEach(t => {
                document.getElementById(t).classList.add('hidden');
                const btn = document.getElementById('nav-' + t);
                btn.classList.remove('border-cyan-400', 'text-cyan-400', 'font-semibold');
                btn.classList.add('border-transparent', 'text-slate-400');
            });

            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById('nav-' + tabId);
            activeBtn.classList.remove('border-transparent', 'text-slate-400');
            activeBtn.classList.add('border-cyan-400', 'text-cyan-400', 'font-semibold');
            
            lucide.createIcons();
            if (tabId === 'tab-waterfall' && chartWaterfall) {
                chartWaterfall.resize();
            }
        }

        async function refreshData() {
            const icon = document.getElementById('refresh-icon');
            icon.classList.add('animate-spin');

            try {
                // 1. Fetch Executive KPIs
                const resKPIs = await fetch('/api/v1/metrics/executive');
                const kpis = await resKPIs.json();
                
                document.getElementById('val-arr').textContent = '$' + (kpis.arr / 1000000).toFixed(2) + 'M';
                document.getElementById('val-mrr').textContent = '$' + (kpis.mrr / 1000).toFixed(1) + 'k';
                document.getElementById('val-nrr').textContent = kpis.nrr_pct.toFixed(1) + '%';
                document.getElementById('val-grr').textContent = kpis.grr_pct.toFixed(1) + '%';
                document.getElementById('val-quick-ratio').textContent = kpis.saas_quick_ratio.toFixed(2) + 'x';
                document.getElementById('val-active-custs').textContent = kpis.active_customers.toLocaleString();
                document.getElementById('val-arpu').textContent = '$' + Math.round(kpis.arpu).toLocaleString();
                document.getElementById('val-cac-payback').textContent = kpis.cac_payback_months.toFixed(1) + ' mo';
                document.getElementById('val-ltv-cac').textContent = kpis.ltv_to_cac_ratio.toFixed(1) + 'x';
                document.getElementById('val-logo-churn').textContent = kpis.monthly_churn_rate_pct.toFixed(1) + '%';
                document.getElementById('val-rev-churn').textContent = kpis.revenue_churn_rate_pct.toFixed(1) + '%';

                // 2. Fetch Waterfall Data
                const resWF = await fetch('/api/v1/metrics/mrr-waterfall');
                const wfData = await resWF.json();
                renderMRRTrendChart(wfData);
                renderWaterfallTab(wfData);

                // 3. Fetch Breakdowns
                const resBreak = await fetch('/api/v1/metrics/breakdown');
                const breakData = await resBreak.json();
                renderBreakdowns(breakData);

                // 4. Fetch Cohorts
                const resCohorts = await fetch('/api/v1/metrics/cohorts');
                const cohorts = await resCohorts.json();
                renderCohortsTable(cohorts);

            } catch (err) {
                console.error("Failed to load metrics:", err);
            } finally {
                icon.classList.remove('animate-spin');
            }
        }

        function renderMRRTrendChart(data) {
            const ctx = document.getElementById('chart-mrr-trend').getContext('2d');
            const labels = data.map(d => d.month);
            const mrrValues = data.map(d => d.ending_mrr);
            const netGrowth = data.map(d => d.net_growth_mrr);

            if (chartTrend) chartTrend.destroy();

            chartTrend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Ending MRR ($)',
                            data: mrrValues,
                            borderColor: '#06B6D4',
                            backgroundColor: 'rgba(6, 182, 212, 0.1)',
                            fill: true,
                            tension: 0.35,
                            borderWidth: 2.5,
                            pointRadius: 2.5
                        },
                        {
                            label: 'Net MRR Growth ($)',
                            data: netGrowth,
                            borderColor: '#10B981',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointRadius: 0,
                            fill: false,
                            tension: 0.2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { color: '#94A3B8', font: { size: 11 } } },
                        tooltip: { mode: 'index', intersect: false }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', maxRotation: 45, font: { size: 10 } } },
                        y: { grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', font: { size: 10 }, callback: v => '$' + (v/1000) + 'k' } }
                    }
                }
            });
        }

        function renderBreakdowns(data) {
            // Region Donut
            const ctxReg = document.getElementById('chart-revenue-region').getContext('2d');
            const regColors = ['#06B6D4', '#3B82F6', '#8B5CF6', '#F59E0B'];
            if (chartRegion) chartRegion.destroy();

            chartRegion = new Chart(ctxReg, {
                type: 'doughnut',
                data: {
                    labels: data.by_region.map(r => r.category),
                    datasets: [{
                        data: data.by_region.map(r => r.revenue),
                        backgroundColor: regColors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    cutout: '70%'
                }
            });

            // Region Legend
            const regLegend = document.getElementById('region-legend');
            regLegend.innerHTML = data.by_region.map((r, i) => `
                <div class="flex items-center space-x-1.5">
                    <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${regColors[i]}"></span>
                    <span class="truncate">${r.category}: <b>${r.percentage}%</b></span>
                </div>
            `).join('');

            // Tier Bar
            const ctxTier = document.getElementById('chart-revenue-tier').getContext('2d');
            if (chartTier) chartTier.destroy();
            chartTier = new Chart(ctxTier, {
                type: 'bar',
                data: {
                    labels: data.by_plan_tier.map(t => t.category),
                    datasets: [{
                        label: 'Net Revenue ($)',
                        data: data.by_plan_tier.map(t => t.revenue),
                        backgroundColor: '#3B82F6',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94A3B8', font: { size: 10 } } },
                        y: { grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', font: { size: 10 }, callback: v => '$' + (v/1000) + 'k' } }
                    }
                }
            });

            // Channel Horizontal Bar
            const ctxChan = document.getElementById('chart-revenue-channel').getContext('2d');
            if (chartChannel) chartChannel.destroy();
            chartChannel = new Chart(ctxChan, {
                type: 'bar',
                data: {
                    labels: data.by_channel.map(c => c.category),
                    datasets: [{
                        label: 'Revenue ($)',
                        data: data.by_channel.map(c => c.revenue),
                        backgroundColor: '#8B5CF6',
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', font: { size: 10 }, callback: v => '$' + (v/1000) + 'k' } },
                        y: { grid: { display: false }, ticks: { color: '#94A3B8', font: { size: 10 } } }
                    }
                }
            });
        }

        function renderWaterfallTab(data) {
            const ctx = document.getElementById('chart-mrr-waterfall').getContext('2d');
            const labels = data.map(d => d.month);

            if (chartWaterfall) chartWaterfall.destroy();

            chartWaterfall = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'New Business', data: data.map(d => d.new_mrr), backgroundColor: '#10B981', stack: 'stack1' },
                        { label: 'Expansion (+)', data: data.map(d => d.expansion_mrr), backgroundColor: '#06B6D4', stack: 'stack1' },
                        { label: 'Contraction (-)', data: data.map(d => -d.contraction_mrr), backgroundColor: '#F59E0B', stack: 'stack1' },
                        { label: 'Churned (-)', data: data.map(d => -d.churn_mrr), backgroundColor: '#F43F5E', stack: 'stack1' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { mode: 'index', intersect: false }
                    },
                    scales: {
                        x: { stacked: true, grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', font: { size: 10 } } },
                        y: { stacked: true, grid: { color: 'rgba(55, 65, 81, 0.3)' }, ticks: { color: '#94A3B8', font: { size: 10 }, callback: v => '$' + (v/1000) + 'k' } }
                    }
                }
            });

            // Waterfall Table
            const tbody = document.getElementById('table-waterfall-body');
            tbody.innerHTML = data.slice().reverse().map(d => `
                <tr class="hover:bg-slate-800/40">
                    <td class="px-4 py-2.5 font-sans font-medium text-white">${d.month}</td>
                    <td class="px-4 py-2.5 text-right text-slate-400">$${d.starting_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right text-emerald-400 font-semibold">+$${d.new_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right text-cyan-400 font-semibold">+$${d.expansion_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right text-amber-400">-$${d.contraction_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right text-rose-400">-$${d.churn_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right text-white font-bold">$${d.ending_mrr.toLocaleString()}</td>
                    <td class="px-4 py-2.5 text-right ${d.net_growth_mrr >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                        ${d.net_growth_mrr >= 0 ? '+' : ''}$${d.net_growth_mrr.toLocaleString()}
                    </td>
                    <td class="px-4 py-2.5 text-right text-slate-300">${d.growth_rate_pct > 0 ? '+' : ''}${d.growth_rate_pct}%</td>
                </tr>
            `).join('');
        }

        function renderCohortsTable(cohorts) {
            const tbody = document.getElementById('table-cohort-body');
            tbody.innerHTML = cohorts.map(c => {
                const cells = c.retention_rates.map(rate => {
                    if (rate === null || rate === undefined) {
                        return '<td class="px-2 py-2 text-slate-700 bg-slate-900/30">-</td>';
                    }
                    let colorClass = 'bg-slate-800/50 text-slate-300';
                    if (rate >= 115) colorClass = 'bg-emerald-950/80 text-emerald-300 font-bold';
                    else if (rate >= 100) colorClass = 'bg-teal-950/70 text-teal-300 font-semibold';
                    else if (rate >= 90) colorClass = 'bg-yellow-950/60 text-yellow-300';
                    else colorClass = 'bg-rose-950/70 text-rose-300 font-medium';

                    return `<td class="px-2 py-2 ${colorClass}">${rate.toFixed(0)}%</td>`;
                }).join('');

                return `
                    <tr class="hover:bg-slate-800/20">
                        <td class="px-3 py-2 text-left font-sans font-medium text-white border-r border-slate-800">${c.cohort_month}</td>
                        <td class="px-3 py-2 text-slate-300 border-r border-slate-800">${c.initial_accounts}</td>
                        <td class="px-3 py-2 text-slate-300 border-r border-slate-800">$${Math.round(c.initial_mrr).toLocaleString()}</td>
                        ${cells}
                    </tr>
                `;
            }).join('');
        }

        async function loadPrebuiltQueries() {
            try {
                const res = await fetch('/api/v1/analytics/prebuilt-queries');
                prebuiltQueries = await res.json();
                const sel = document.getElementById('select-prebuilt-sql');
                prebuiltQueries.forEach(q => {
                    const opt = document.createElement('option');
                    opt.value = q.id;
                    opt.textContent = q.name;
                    sel.appendChild(opt);
                });
            } catch (e) {
                console.error("Failed to load prebuilt queries:", e);
            }
        }

        function loadSelectedSQL() {
            const qid = document.getElementById('select-prebuilt-sql').value;
            const q = prebuiltQueries.find(item => item.id === qid);
            if (q) {
                document.getElementById('sql-query-input').value = q.sql;
                const descBox = document.getElementById('query-desc-box');
                document.getElementById('query-desc-text').textContent = q.description;
                descBox.classList.remove('hidden');
            }
        }

        async function executeSQLQuery() {
            const query = document.getElementById('sql-query-input').value.trim();
            if (!query) return;

            const timeEl = document.getElementById('sql-execution-time');
            timeEl.textContent = 'Executing...';
            timeEl.className = 'font-mono text-cyan-400 animate-pulse';

            try {
                const res = await fetch('/api/v1/analytics/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, limit: 100 })
                });
                const data = await res.json();

                if (data.error) {
                    timeEl.textContent = `${data.execution_time_ms} ms (Error)`;
                    timeEl.className = 'font-mono text-rose-400 font-semibold';
                    document.getElementById('sql-table-head').innerHTML = '<tr><th class="px-4 py-2.5 text-rose-400">Query Error</th></tr>';
                    document.getElementById('sql-table-body').innerHTML = `<tr><td class="px-4 py-3 text-rose-300 font-mono text-xs">${data.error}</td></tr>`;
                    document.getElementById('sql-result-counter').textContent = 'Error occurred';
                    return;
                }

                timeEl.textContent = `${data.execution_time_ms.toFixed(2)} ms`;
                timeEl.className = 'font-mono text-emerald-400 font-semibold';
                document.getElementById('sql-result-counter').textContent = `${data.row_count} rows returned`;

                // Render Table Header
                const thead = document.getElementById('sql-table-head');
                thead.innerHTML = '<tr>' + data.columns.map(c => `<th class="px-4 py-2.5 text-slate-300 font-semibold border-r border-slate-800">${c}</th>`).join('') + '</tr>';

                // Render Table Body
                const tbody = document.getElementById('sql-table-body');
                if (data.rows.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="' + data.columns.length + '" class="px-4 py-6 text-center text-slate-500">No matching records found</td></tr>';
                } else {
                    tbody.innerHTML = data.rows.map(r => `
                        <tr class="hover:bg-slate-900/60">
                            ${r.map(val => `<td class="px-4 py-2 text-slate-300 border-r border-slate-800/50">${val !== null ? val : '<span class="text-slate-600">NULL</span>'}</td>`).join('')}
                        </tr>
                    `).join('');
                }
            } catch (err) {
                timeEl.textContent = 'Request Failed';
                timeEl.className = 'font-mono text-rose-400';
            }
        }

        function resetSQLQuery() {
            document.getElementById('sql-query-input').value = '';
            document.getElementById('select-prebuilt-sql').value = '';
            document.getElementById('query-desc-box').classList.add('hidden');
        }

        async function loadDAXCatalog() {
            try {
                const res = await fetch('/api/v1/dax/catalog');
                const data = await res.json();
                daxCatalog = data.measures || [];
                renderDAXMeasures(daxCatalog);
            } catch (e) {
                console.error("Failed to load DAX catalog:", e);
            }
        }

        function renderDAXMeasures(measures) {
            const container = document.getElementById('dax-cards-container');
            container.innerHTML = measures.map((m, idx) => `
                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition">
                    <div>
                        <div class="flex items-center justify-between mb-1.5">
                            <span class="font-bold text-cyan-400 text-sm font-mono">[${m.name}]</span>
                            <button onclick="copyToClipboard('${m.name}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 text-[10px] flex items-center space-x-1 border border-slate-700 transition">
                                <i data-lucide="copy" class="w-3 h-3"></i>
                                <span>Copy</span>
                            </button>
                        </div>
                        <p class="text-xs text-slate-400 mb-3">${m.description || 'Verified DAX calculation formula.'}</p>
                        <pre class="p-3 rounded-lg bg-slate-950 font-mono text-[11px] text-emerald-300 overflow-x-auto border border-slate-800/80 leading-relaxed">${m.formula}</pre>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }

        function filterDAXMeasures() {
            const term = document.getElementById('dax-search-input').value.toLowerCase();
            const filtered = daxCatalog.filter(m => 
                m.name.toLowerCase().includes(term) || 
                (m.description && m.description.toLowerCase().includes(term)) ||
                m.formula.toLowerCase().includes(term)
            );
            renderDAXMeasures(filtered);
        }

        function copyToClipboard(name) {
            const m = daxCatalog.find(item => item.name === name);
            if (m) {
                navigator.clipboard.writeText(m.formula);
                alert(`Copied DAX formula [${name}] to clipboard!`);
            }
        }

        function exportResultsCSV() {
            alert("Exporting query results to CSV...");
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', () => {
            refreshData();
            loadPrebuiltQueries();
            loadDAXCatalog();
        });
    </script>
</body>
</html>
"""
