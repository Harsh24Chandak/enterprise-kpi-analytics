"""
High-throughput synthetic data generator for enterprise B2B SaaS revenue operations.
Simulates 100,000 transactions across 24 rolling months with realistic cohort dynamics,
expansion/contraction patterns, multi-tier pricing, and multi-region attribution.
"""
import random
import datetime
from typing import Dict, List, Tuple, Any

PLAN_TIERS = {
    "tier_starter": {"name": "Starter", "tier_level": 1, "base_price": 299.0, "billing_cycle": "Monthly"},
    "tier_growth": {"name": "Growth", "tier_level": 2, "base_price": 999.0, "billing_cycle": "Monthly"},
    "tier_enterprise": {"name": "Enterprise", "tier_level": 3, "base_price": 2999.0, "billing_cycle": "Monthly"},
    "tier_ultimate": {"name": "Ultimate", "tier_level": 4, "base_price": 7499.0, "billing_cycle": "Monthly"}
}

CHANNELS = {
    "chan_organic": {"name": "Organic Search", "category": "Inbound", "cac_range": (1200, 2400), "conv_rate": 0.042},
    "chan_plg": {"name": "Product-Led Growth", "category": "Self-Serve", "cac_range": (800, 1800), "conv_rate": 0.068},
    "chan_paid": {"name": "Paid Performance", "category": "Outbound", "cac_range": (3500, 6200), "conv_rate": 0.028},
    "chan_direct": {"name": "Direct Enterprise Sales", "category": "Enterprise", "cac_range": (8500, 16000), "conv_rate": 0.019},
    "chan_partner": {"name": "Partner Referrals", "category": "Channel", "cac_range": (2800, 4800), "conv_rate": 0.035}
}

INDUSTRIES = [
    "Fintech & Payments", "Healthcare AI", "Cybersecurity", 
    "Cloud Infrastructure", "E-Commerce Enterprise", "MarTech & Analytics"
]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]

COMPANY_PREFIXES = [
    "Apex", "Vertex", "Hyper", "Nova", "Stratos", "Quantum", "Pulse", "Nexus",
    "Aura", "Synergy", "Zenith", "Catalyst", "Optima", "Vector", "Vanguard",
    "Omni", "Prism", "Beacon", "Solas", "Element", "Krypton", "Helix", "Iron", "Titan"
]

COMPANY_SUFFIXES = [
    "Technologies", "Systems", "Cloud", "Analytics", "Networks", "Labs",
    "Software", "Solutions", "Dynamics", "Platform", "Data", "Security", "Scale", "Robotics"
]

def generate_month_series(start_year: int = 2024, start_month: int = 11, total_months: int = 24) -> List[str]:
    """Generates YYYY-MM formatted string list for 24 months."""
    months = []
    y, m = start_year, start_month
    for _ in range(total_months):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months

def generate_synthetic_enterprise_data(
    num_customers: int = 1200,
    target_transactions: int = 100000,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates all dimensional entities and facts:
    Returns (dim_customers, dim_products, dim_channels, dim_dates, fact_transactions, fact_snapshots)
    """
    random.seed(seed)
    months = generate_month_series(2024, 11, 24)
    
    # 1. Dimension: Products
    dim_products = []
    for pid, pdata in PLAN_TIERS.items():
        dim_products.append({
            "product_id": pid,
            "product_name": pdata["name"],
            "tier_level": pdata["tier_level"],
            "base_price": pdata["base_price"],
            "billing_cycle": pdata["billing_cycle"]
        })
        
    # 2. Dimension: Channels
    dim_channels = []
    for cid, cdata in CHANNELS.items():
        dim_channels.append({
            "channel_id": cid,
            "channel_name": cdata["name"],
            "acquisition_category": cdata["category"],
            "avg_conversion_rate": cdata["conv_rate"],
            "cost_multiplier": round(cdata["cac_range"][1] / 5000.0, 2)
        })
        
    # 3. Dimension: Dates (Full daily calendar across 2 years)
    dim_dates = []
    start_date = datetime.date(2024, 11, 1)
    end_date = datetime.date(2026, 10, 31)
    cur = start_date
    date_keys_by_month: Dict[str, List[int]] = {m: [] for m in months}
    
    while cur <= end_date:
        dkey = int(cur.strftime("%Y%m%d"))
        ym = cur.strftime("%Y-%m")
        if ym in date_keys_by_month:
            date_keys_by_month[ym].append(dkey)
        
        # Determine fiscal period (Assuming standard FY calendar)
        f_quarter = f"FY{(cur.year if cur.month >= 2 else cur.year - 1)}-Q{(cur.month - 1) // 3 + 1}"
        f_year = f"FY{cur.year}"
        
        dim_dates.append({
            "date_key": dkey,
            "full_date": cur.isoformat(),
            "year": cur.year,
            "quarter": (cur.month - 1) // 3 + 1,
            "month": cur.month,
            "month_name": cur.strftime("%B"),
            "day": cur.day,
            "day_of_week": cur.weekday(),
            "day_name": cur.strftime("%A"),
            "is_weekend": 1 if cur.weekday() >= 5 else 0,
            "fiscal_year": f_year,
            "fiscal_quarter": f_quarter
        })
        cur += datetime.timedelta(days=1)
        
    # 4. Dimension: Customers & Cohorts
    tier_keys = list(PLAN_TIERS.keys())
    tier_weights = [0.45, 0.32, 0.18, 0.05]  # Starter, Growth, Enterprise, Ultimate
    channel_keys = list(CHANNELS.keys())
    channel_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    
    dim_customers = []
    customer_profiles = {}
    
    for i in range(1, num_customers + 1):
        cid = f"cust_{i:05d}"
        cname = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)} {random.randint(10, 99)}"
        industry = random.choice(INDUSTRIES)
        region = random.choices(REGIONS, weights=[0.50, 0.28, 0.15, 0.07])[0]
        init_tier = random.choices(tier_keys, weights=tier_weights)[0]
        channel = random.choices(channel_keys, weights=channel_weights)[0]
        
        # Signup month skewed towards earlier months to allow rich cohort retention curves
        # e.g. vintage months 0 to 18
        signup_month_idx = random.randint(0, len(months) - 6)
        signup_month = months[signup_month_idx]
        
        cac_min, cac_max = CHANNELS[channel]["cac_range"]
        cac_val = round(random.uniform(cac_min, cac_max) * (1.0 + (PLAN_TIERS[init_tier]["tier_level"] - 1) * 0.4), 2)
        health_score = round(random.uniform(55, 98), 1)
        
        dim_customers.append({
            "customer_id": cid,
            "customer_name": cname,
            "industry": industry,
            "plan_tier": init_tier,
            "region": region,
            "channel_id": channel,
            "signup_date": f"{signup_month}-01",
            "cac": cac_val,
            "health_score": health_score,
            "status": "Active"
        })
        
        customer_profiles[cid] = {
            "current_tier": init_tier,
            "signup_idx": signup_month_idx,
            "active": True,
            "churn_month": None,
            "health_score": health_score,
            "channel": channel,
            "region": region
        }
        
    # 5. Transactions & Monthly Snapshots Generation
    fact_transactions = []
    fact_snapshots = []
    tx_counter = 1
    
    # Track customer previous month MRR
    for cid, prof in customer_profiles.items():
        prof["prev_mrr"] = 0.0

    for m_idx, ym in enumerate(months):
        for cid, prof in customer_profiles.items():
            if m_idx < prof["signup_idx"]:
                # Not signed up yet
                continue
                
            prev_m = prof["prev_mrr"]
            cur_tier_data = PLAN_TIERS[prof["current_tier"]]
            base_amount = cur_tier_data["base_price"]
            
            exp_amt = 0.0
            con_amt = 0.0
            churn_amt = 0.0
            
            if m_idx == prof["signup_idx"]:
                # Brand new customer in their signup vintage month
                change_type = "New"
                prof["active"] = True
                active_mrr = base_amount
                prof["prev_mrr"] = active_mrr
            elif not prof["active"]:
                # Previously churned: small chance of reactivation (1.5%)
                if random.random() < 0.015:
                    prof["active"] = True
                    prof["churn_month"] = None
                    change_type = "Expansion"
                    exp_amt = base_amount
                    active_mrr = base_amount
                    prof["prev_mrr"] = active_mrr
                else:
                    continue
            else:
                # Existing active customer from prior month
                change_type = "Unchanged"
                churn_hazard = 0.035 if prof["current_tier"] == "tier_starter" else 0.018
                if prof["health_score"] < 65:
                    churn_hazard *= 2.2
                    
                if random.random() < churn_hazard:
                    prof["active"] = False
                    prof["churn_month"] = ym
                    change_type = "Churn"
                    active_mrr = 0.0
                    churn_amt = prev_m
                    prof["prev_mrr"] = 0.0
                else:
                    # Expansion probability (8%)
                    current_lvl = PLAN_TIERS[prof["current_tier"]]["tier_level"]
                    if random.random() < 0.08 and current_lvl < 4:
                        next_tier = [k for k, v in PLAN_TIERS.items() if v["tier_level"] == current_lvl + 1][0]
                        prof["current_tier"] = next_tier
                        new_tier_data = PLAN_TIERS[next_tier]
                        active_mrr = new_tier_data["base_price"]
                        exp_amt = round(active_mrr - prev_m, 2)
                        change_type = "Expansion"
                        prof["prev_mrr"] = active_mrr
                    # Contraction probability (3%)
                    elif random.random() < 0.03 and current_lvl > 1:
                        prev_tier = [k for k, v in PLAN_TIERS.items() if v["tier_level"] == current_lvl - 1][0]
                        prof["current_tier"] = prev_tier
                        new_tier_data = PLAN_TIERS[prev_tier]
                        active_mrr = new_tier_data["base_price"]
                        con_amt = round(prev_m - active_mrr, 2)
                        change_type = "Contraction"
                        prof["prev_mrr"] = active_mrr
                    else:
                        active_mrr = prev_m
            
            # Record Snapshot
            fact_snapshots.append({
                "snapshot_month": ym,
                "customer_id": cid,
                "plan_tier": prof["current_tier"],
                "active_mrr": active_mrr,
                "mrr_change_type": change_type,
                "expansion_amount": exp_amt,
                "contraction_amount": con_amt,
                "churn_amount": churn_amt,
                "net_mrr": active_mrr
            })
            
            # If churned, no transaction this month
            if not prof["active"] and change_type == "Churn":
                continue
                
            # Subscription billing transaction
            m_date_keys = date_keys_by_month.get(ym, [20250101])
            billing_dkey = random.choice(m_date_keys)
            
            discount = 0.0
            if random.random() < 0.12:
                discount = round(active_mrr * random.choice([0.10, 0.15, 0.20]), 2)
                
            refund = 0.0
            if random.random() < 0.011:
                refund = round(active_mrr * random.uniform(0.5, 1.0), 2)
                
            net_amt = round(max(0.0, active_mrr - discount - refund), 2)
            
            fact_transactions.append({
                "transaction_id": f"txn_{tx_counter:07d}",
                "date_key": billing_dkey,
                "customer_id": cid,
                "product_id": prof["current_tier"],
                "channel_id": prof["channel"],
                "event_type": "subscription_billing",
                "gross_amount": active_mrr,
                "discount_amount": discount,
                "refund_amount": refund,
                "net_amount": net_amt,
                "payment_status": "settled",
                "currency": "USD"
            })
            tx_counter += 1
            
    # Granular usage transactions to reach target_transactions
    active_cids = [cid for cid, p in customer_profiles.items() if p["active"]]
    all_dkeys = [d["date_key"] for d in dim_dates]
    needed_usage_txs = max(0, target_transactions - len(fact_transactions))
    
    event_subtypes = [
        ("api_overage", 25.0, 150.0),
        ("compute_burst", 45.0, 320.0),
        ("seat_license_add", 120.0, 600.0),
        ("storage_expansion", 30.0, 180.0),
        ("priority_support", 150.0, 500.0)
    ]
    
    for _ in range(needed_usage_txs):
        cid = random.choice(active_cids)
        prof = customer_profiles[cid]
        ev_type, min_p, max_p = random.choice(event_subtypes)
        g_amt = round(random.uniform(min_p, max_p), 2)
        dkey = random.choice(all_dkeys)
        
        disc = 0.0
        if random.random() < 0.05:
            disc = round(g_amt * 0.1, 2)
            
        fact_transactions.append({
            "transaction_id": f"txn_{tx_counter:07d}",
            "date_key": dkey,
            "customer_id": cid,
            "product_id": prof["current_tier"],
            "channel_id": prof["channel"],
            "event_type": ev_type,
            "gross_amount": g_amt,
            "discount_amount": disc,
            "refund_amount": 0.0,
            "net_amount": round(g_amt - disc, 2),
            "payment_status": "settled",
            "currency": "USD"
        })
        tx_counter += 1

    return dim_customers, dim_products, dim_channels, dim_dates, fact_transactions, fact_snapshots
