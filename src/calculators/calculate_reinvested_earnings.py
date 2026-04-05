#!/usr/bin/env python3
"""
Calculate Retained Earnings Flow (Quarterly Changes)
Flow = Retained Earnings (Current Q) - Retained Earnings (Previous Q)
"""

import json
import pandas as pd
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

FLOW_CSV_PATH = "data/results/retained_earnings_flow.csv"
FLOW_JSON_PATH = "data/results/retained_earnings_flow.json"

_STMT_TYPE_ORDER = {"annual": 0, "q1": 1, "q2": 2, "q3": 3, "q4": 4}


def _find_statement(statements: List[Dict], stype: str, year: int):
    return next((s for s in statements if s["type"] == stype and s["year"] == year), None)


def _append_flow(
    flows: List[Dict],
    quarter: str,
    year: int,
    current: Optional[Dict],
    previous: Optional[Dict],
    formula: str,
) -> None:
    if current is None or previous is None:
        return
    flows.append(
        {
            "quarter": quarter,
            "year": year,
            "current_value": current["value"],
            "previous_value": previous["value"],
            "flow": current["value"] - previous["value"],
            "flow_formula": formula,
        }
    )


def _quarterly_flows_for_year(statements: List[Dict], current_year: int) -> List[Dict]:
    flows: List[Dict] = []
    q1 = _find_statement(statements, "q1", current_year)
    annual_prev = _find_statement(statements, "annual", current_year - 1)
    _append_flow(
        flows,
        "Q1",
        current_year,
        q1,
        annual_prev,
        f"Q1 {current_year} - Annual {current_year - 1}",
    )
    q2 = _find_statement(statements, "q2", current_year)
    _append_flow(
        flows,
        "Q2",
        current_year,
        q2,
        q1,
        f"Q2 {current_year} - Q1 {current_year}",
    )
    q3 = _find_statement(statements, "q3", current_year)
    _append_flow(
        flows,
        "Q3",
        current_year,
        q3,
        q2,
        f"Q3 {current_year} - Q2 {current_year}",
    )
    q4 = _find_statement(statements, "q4", current_year)
    _append_flow(
        flows,
        "Q4",
        current_year,
        q4,
        q3,
        f"Q4 {current_year} - Q3 {current_year}",
    )
    return flows


def parse_statement_info(filename: str) -> Optional[Dict[str, Any]]:
    """Parse PDF filename to extract company, statement type, and year"""
    # Example: 2222_q1_2025.pdf -> company: 2222, type: q1, year: 2025
    # Example: 2382_annual_2024.pdf -> company: 2382, type: annual, year: 2024

    parts = filename.replace(".pdf", "").split("_")
    if len(parts) >= 3:
        company = parts[0]
        statement_type = parts[1]
        year = int(parts[2])

        return {
            "company": company,
            "type": statement_type,
            "year": year,
        }
    return None

def calculate_retained_earnings_flow(retained_data: List[Dict]) -> List[Dict]:
    """Calculate quarterly flow of retained earnings"""
    
    # Group by company
    companies = {}
    for item in retained_data:
        if not item.get('success'):
            continue
            
        company = item['company_symbol']
        if company not in companies:
            companies[company] = []
        
        # Parse statement info
        info = parse_statement_info(item['pdf_filename'])
        if not info:
            continue
            
        companies[company].append({
            'type': info['type'],
            'year': info['year'],
            'value': item['numeric_value'],
            'pdf_filename': item['pdf_filename']
        })
    
    flow_results = []
    
    for company, statements in companies.items():
        statements.sort(key=lambda x: (x["year"], _STMT_TYPE_ORDER.get(x["type"], 999)))
        if not statements:
            continue
        current_year = max(s["year"] for s in statements)
        for flow in _quarterly_flows_for_year(statements, current_year):
            flow_results.append(
                {
                    "company_symbol": company,
                    "quarter": flow["quarter"],
                    "year": flow["year"],
                    "current_value": flow["current_value"],
                    "previous_value": flow["previous_value"],
                    "flow": flow["flow"],
                    "flow_formula": flow["flow_formula"],
                }
            )
    
    return flow_results


_FINAL_FLOW_COLUMNS = [
    "company_symbol",
    "company_name",
    "quarter",
    "year",
    "current_value",
    "previous_value",
    "flow",
    "flow_formula",
    "foreign_ownership",
    "max_allowed",
    "investor_limit",
    "reinvested_earnings_flow",
    "net_profit_foreign_investor",
    "distributed_profits_foreign_investor",
]


def _reinvested_earnings_from_row(row) -> float:
    if not (pd.notna(row["flow"]) and pd.notna(row["investor_limit"])):
        return 0
    lim = str(row["investor_limit"]).replace("%", "")
    if not lim.replace(".", "").isdigit():
        return 0
    pct = float(lim)
    if pct <= 0:
        return 0
    return row["flow"] * (pct / 100)


def _investor_limit_fraction(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).replace("%", "")
    if not s.replace(".", "").isdigit():
        return 0.0
    try:
        return float(s) / 100.0
    except Exception:
        return 0.0


def _net_profit_lookup_from_raw(net_profit_data: List[Dict]) -> Dict[str, Any]:
    lookup: Dict[str, Any] = {}
    for company in net_profit_data:
        symbol = company.get("company_symbol")
        if symbol:
            lookup[symbol] = company
    return lookup


def _raw_net_profit_for_row(lookup: Dict[str, Any], symbol: str, quarter: str, year: int):
    company = lookup.get(str(symbol), {})
    qmap = company.get("quarterly_net_profit", {}) if company else {}
    if not qmap:
        return None
    return qmap.get(f"{quarter} {year}", None)


def _load_retained_results():
    try:
        with open("data/results/retained_earnings_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} retained earnings records")
        return data
    except FileNotFoundError:
        print("❌ Error: retained_earnings_results.json not found")
        print("Please run the main extraction script first")
        return None
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def _load_ownership_dataframe() -> pd.DataFrame:
    try:
        with open("data/ownership/foreign_ownership_data.json", "r", encoding="utf-8") as f:
            ownership_json = json.load(f)
        ownership_df = pd.DataFrame(ownership_json)
        print(f"✅ Loaded ownership data (JSON) for {len(ownership_df)} companies")
    except FileNotFoundError:
        ownership_df = pd.read_csv("data/ownership/foreign_ownership_data.csv")
        print(f"✅ Loaded ownership data (CSV) for {len(ownership_df)} companies")
    if "symbol" not in ownership_df.columns and "company_symbol" in ownership_df.columns:
        ownership_df = ownership_df.rename(columns={"company_symbol": "symbol"})
    return ownership_df


def _merge_flow_with_ownership(flow_df: pd.DataFrame, ownership_df: pd.DataFrame) -> pd.DataFrame:
    fd = flow_df.copy()
    fd["company_symbol"] = fd["company_symbol"].astype(str)
    od = ownership_df.copy()
    od["symbol"] = od["symbol"].astype(str)
    merged = pd.merge(
        fd,
        od[["symbol", "company_name", "foreign_ownership", "max_allowed", "investor_limit"]],
        left_on="company_symbol",
        right_on="symbol",
        how="left",
        validate="many_to_one",
    )
    merged["reinvested_earnings_flow"] = merged.apply(_reinvested_earnings_from_row, axis=1)
    return merged


def _apply_net_profit_columns(merged: pd.DataFrame) -> pd.DataFrame:
    try:
        with open("data/results/quarterly_net_profit.json", "r", encoding="utf-8") as f:
            net_profit_data = json.load(f)
        print(f"✅ Loaded net profit data for {len(net_profit_data)} companies")
        lookup = _net_profit_lookup_from_raw(net_profit_data)
        m = merged.copy()
        m["__raw_net_profit"] = m.apply(
            lambda row: _raw_net_profit_for_row(
                lookup, row["company_symbol"], row["quarter"], row["year"]
            ),
            axis=1,
        )
        m["__inv_frac"] = m["investor_limit"].apply(_investor_limit_fraction)
        m["__net_profit_foreign_investor_calc"] = m.apply(
            lambda row: (
                (row["__raw_net_profit"] if row["__raw_net_profit"] is not None else 0)
                * row["__inv_frac"]
            ),
            axis=1,
        )
        m["net_profit_foreign_investor"] = m.apply(
            lambda row: (
                row["__net_profit_foreign_investor_calc"]
                if row["__raw_net_profit"] is not None
                else ""
            ),
            axis=1,
        )
        m["distributed_profits_foreign_investor"] = m.apply(
            lambda row: (
                row["__net_profit_foreign_investor_calc"] - row["reinvested_earnings_flow"]
                if pd.notna(row["reinvested_earnings_flow"])
                else 0
            ),
            axis=1,
        )
        print("✅ Added net profit calculations for foreign investors")
        return m[_FINAL_FLOW_COLUMNS].copy()
    except FileNotFoundError:
        print("⚠️ Warning: quarterly_net_profit.json not found, skipping net profit calculations")
        m = merged.copy()
        m["net_profit_foreign_investor"] = 0
        m["distributed_profits_foreign_investor"] = 0
        return m[_FINAL_FLOW_COLUMNS].copy()
    except Exception as e:
        print(f"⚠️ Warning: Error processing net profit data: {e}")
        m = merged.copy()
        m["net_profit_foreign_investor"] = 0
        m["distributed_profits_foreign_investor"] = 0
        return m[_FINAL_FLOW_COLUMNS].copy()


def _save_flow_outputs(final_results: pd.DataFrame) -> None:
    final_results.to_csv(FLOW_CSV_PATH, index=False, encoding="utf-8")
    print(f"✅ Saved flow data to {FLOW_CSV_PATH}")
    final_results.to_json(FLOW_JSON_PATH, orient="records", force_ascii=False, indent=2)
    print(f"✅ Saved flow data to {FLOW_JSON_PATH}")
    compact = final_results[
        [
            "company_symbol",
            "company_name",
            "quarter",
            "year",
            "reinvested_earnings_flow",
            "net_profit_foreign_investor",
            "distributed_profits_foreign_investor",
        ]
    ].copy()
    compact_json_path = "data/results/foreign_investor_results.json"
    compact.to_json(compact_json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Saved foreign investor metrics to {compact_json_path}")


def _print_sample_flow_results(final_results: pd.DataFrame) -> None:
    print("\n📊 Sample Flow Results:")
    print("=" * 80)
    for _, row in final_results.head(10).iterrows():
        print(f"Company: {row['company_name']} ({row['company_symbol']})")
        print(f"Quarter: {row['quarter']} {row['year']}")
        print(f"Flow: {row['flow']:,.0f} SAR ({row['flow_formula']})")
        print(f"Foreign Investor Flow: {row['reinvested_earnings_flow']:,.2f} SAR")
        print(f"Net Profit for Foreign Investor: {row['net_profit_foreign_investor']:,.2f} SAR")
        print(f"Distributed Profits for Foreign Investor: {row['distributed_profits_foreign_investor']:,.2f} SAR")
        print("-" * 40)


def _save_basic_flow_only(flow_df: pd.DataFrame) -> None:
    flow_df.to_csv(FLOW_CSV_PATH, index=False, encoding="utf-8")
    print(f"✅ Saved basic flow data to {FLOW_CSV_PATH}")
    flow_df.to_json(FLOW_JSON_PATH, orient="records", force_ascii=False, indent=2)
    print(f"✅ Saved basic flow data to {FLOW_JSON_PATH}")


def main():
    """Main function to calculate retained earnings flow"""
    print("🔄 Calculating Retained Earnings Flow (Quarterly Changes)")
    print("=" * 60)

    retained_data = _load_retained_results()
    if retained_data is None:
        return

    print("🔄 Calculating quarterly flows...")
    flow_results = calculate_retained_earnings_flow(retained_data)
    if not flow_results:
        print("❌ No flows could be calculated")
        return

    flow_df = pd.DataFrame(flow_results)

    try:
        ownership_df = _load_ownership_dataframe()
        merged = _merge_flow_with_ownership(flow_df, ownership_df)
        final_results = _apply_net_profit_columns(merged)
        print(f"✅ Calculated flows for {len(final_results)} company-quarters")
        print("✅ Added foreign investor flow calculations")
        _save_flow_outputs(final_results)
        _print_sample_flow_results(final_results)
    except FileNotFoundError:
        print("⚠️ Warning: ownership data not found, saving basic flow data only")
        _save_basic_flow_only(flow_df)
    except Exception as e:
        print(f"❌ Error processing ownership data: {e}")
        flow_df.to_csv(FLOW_CSV_PATH, index=False, encoding="utf-8")
        print(f"✅ Saved basic flow data to {FLOW_CSV_PATH}")

    print("\n🎉 Flow calculation completed successfully!")

if __name__ == "__main__":
    main() 