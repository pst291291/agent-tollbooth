import os
import json

BASE_DIR = r"C:\Users\Admin\.gemini\antigravity\scratch\agent_tollbooth"

# Fee & Traffic Tiers
SCENARIOS = [
    {
        "tier": "Tier 1: Early Beta (Niche Tooling)",
        "daily_calls": 25000,
        "avg_call_price_usd": 0.0025,
        "toll_fee_pct": 5.0,
        "infra_cost_monthly_usd": 50.0
    },
    {
        "tier": "Tier 2: Production Gateway (50 Integrated Agent Tools)",
        "daily_calls": 250000,
        "avg_call_price_usd": 0.0025,
        "toll_fee_pct": 5.0,
        "infra_cost_monthly_usd": 150.0
    },
    {
        "tier": "Tier 3: Ecosystem Hub (AgentKit & x402 Default Relayer)",
        "daily_calls": 2500000,
        "avg_call_price_usd": 0.0020,
        "toll_fee_pct": 3.5,
        "infra_cost_monthly_usd": 500.0
    },
    {
        "tier": "Tier 4: Global Machine-to-Machine Backplane",
        "daily_calls": 25000000,
        "avg_call_price_usd": 0.0015,
        "toll_fee_pct": 2.5,
        "infra_cost_monthly_usd": 2500.0
    },
    {
        "tier": "Tier 5: Planetary Autonomous Swarm Economy",
        "daily_calls": 250000000,
        "avg_call_price_usd": 0.0010,
        "toll_fee_pct": 1.5,
        "infra_cost_monthly_usd": 15000.0
    }
]

def calculate_economics():
    results = []
    for s in SCENARIOS:
        daily_calls = s["daily_calls"]
        price = s["avg_call_price_usd"]
        toll_pct = s["toll_fee_pct"] / 100.0
        infra_month = s["infra_cost_monthly_usd"]

        daily_volume_usd = daily_calls * price
        monthly_volume_usd = daily_volume_usd * 30.416
        annual_volume_usd = daily_volume_usd * 365.0

        daily_gross_toll = daily_volume_usd * toll_pct
        monthly_gross_toll = monthly_volume_usd * toll_pct
        annual_gross_toll = annual_volume_usd * toll_pct

        monthly_net_profit = monthly_gross_toll - infra_month
        annual_net_profit = (daily_gross_toll * 365.0) - (infra_month * 12.0)

        # In GBP at 1.30 USD/GBP
        annual_net_gbp = annual_net_profit / 1.30
        weekly_payout_gbp = annual_net_gbp / 52.0

        results.append({
            "tier_name": s["tier"],
            "daily_agent_calls": f"{daily_calls:,}",
            "avg_price_per_call": f"${price:.4f}",
            "toll_rate": f"{s['toll_fee_pct']}%",
            "daily_gross_volume_usd": f"${daily_volume_usd:,.2f}",
            "daily_toll_revenue_usd": f"${daily_gross_toll:,.2f}",
            "monthly_net_profit_usd": f"${monthly_net_profit:,.2f}",
            "annual_net_profit_usd": f"${annual_net_profit:,.2f}",
            "annual_net_profit_gbp": f"£{annual_net_gbp:,.2f}",
            "weekly_cashflow_gbp": f"£{weekly_payout_gbp:,.2f}",
            "charity_checks_per_week_at_10k": int(weekly_payout_gbp / 10000.0) if weekly_payout_gbp >= 10000 else 0
        })

    out_file = os.path.join(BASE_DIR, "tollbooth_economic_projections.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    res = calculate_economics()
    print("==================================================================")
    print("      AGENTIC TOLLBOOTH ECONOMIC PROJECTIONS & SCALING TIERS     ")
    print("==================================================================")
    for r in res:
        print(f"\n{r['tier_name']}:")
        print(f"  Calls/Day: {r['daily_agent_calls']} | Daily Volume: {r['daily_gross_volume_usd']}")
        print(f"  Daily Toll Revenue: {r['daily_toll_revenue_usd']} ({r['toll_rate']} take-rate)")
        print(f"  Annual Net Profit:  {r['annual_net_profit_usd']} ({r['annual_net_profit_gbp']})")
        print(f"  Weekly Cashflow:    {r['weekly_cashflow_gbp']} / week")
        if r['charity_checks_per_week_at_10k'] > 0:
            print(f"  [CHARITY IMPACT] Can fund {r['charity_checks_per_week_at_10k']} £10k charity cheques EVERY SINGLE WEEK!")
    print("==================================================================")
