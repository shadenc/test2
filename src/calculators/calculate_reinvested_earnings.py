#!/usr/bin/env python3
"""
Calculate Retained Earnings Flow (Quarterly Changes)
Flow = Retained Earnings (Current Q) - Retained Earnings (Previous Q)
"""

import json
import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional

def parse_statement_info(filename: str) -> Dict:
    """Parse PDF filename to extract company, statement type, and year"""
    # Example: 2222_q1_2025.pdf -> company: 2222, type: q1, year: 2025
    # Example: 2382_annual_2024.pdf -> company: 2382, type: annual, year: 2024
    
    parts = filename.replace('.pdf', '').split('_')
    if len(parts) >= 3:
        company = parts[0]
        statement_type = parts[1]
        year = int(parts[2])
        
        return {
            'company': company,
            'type': statement_type,
            'year': year
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
        # Sort statements by year and type (annual first, then q1, q2, q3, q4)
        type_order = {'annual': 0, 'q1': 1, 'q2': 2, 'q3': 3, 'q4': 4}
        statements.sort(key=lambda x: (x['year'], type_order.get(x['type'], 999)))
        
        # Find current year (most recent year with data)
        if not statements:
            continue
            
        current_year = max(s['year'] for s in statements)
        
        # Calculate flows for current year
        flows = []
        
        # Q1 Flow = Q1 current year - Annual previous year
        q1_current = next((s for s in statements if s['type'] == 'q1' and s['year'] == current_year), None)
        annual_previous = next((s for s in statements if s['type'] == 'annual' and s['year'] == current_year - 1), None)
        
        if q1_current and annual_previous:
            q1_flow = q1_current['value'] - annual_previous['value']
            flows.append({
                'quarter': 'Q1',
                'year': current_year,
                'current_value': q1_current['value'],
                'previous_value': annual_previous['value'],
                'flow': q1_flow,
                'flow_formula': f"Q1 {current_year} - Annual {current_year-1}"
            })
        
        # Q2 Flow = Q2 current year - Q1 current year
        q2_current = next((s for s in statements if s['type'] == 'q2' and s['year'] == current_year), None)
        if q2_current and q1_current:
            q2_flow = q2_current['value'] - q1_current['value']
            flows.append({
                'quarter': 'Q2',
                'year': current_year,
                'current_value': q2_current['value'],
                'previous_value': q1_current['value'],
                'flow': q2_flow,
                'flow_formula': f"Q2 {current_year} - Q1 {current_year}"
            })
        
        # Q3 Flow = Q3 current year - Q2 current year
        q3_current = next((s for s in statements if s['type'] == 'q3' and s['year'] == current_year), None)
        if q3_current and q2_current:
            q3_flow = q3_current['value'] - q2_current['value']
            flows.append({
                'quarter': 'Q3',
                'year': current_year,
                'current_value': q3_current['value'],
                'previous_value': q2_current['value'],
                'flow': q3_flow,
                'flow_formula': f"Q3 {current_year} - Q2 {current_year}"
            })
        
        # Q4 Flow = Q4 current year - Q3 current year
        q4_current = next((s for s in statements if s['type'] == 'q4' and s['year'] == current_year), None)
        if q4_current and q3_current:
            q4_flow = q4_current['value'] - q3_current['value']
            flows.append({
                'quarter': 'Q4',
                'year': current_year,
                'current_value': q4_current['value'],
                'previous_value': q3_current['value'],
                'flow': q4_flow,
                'flow_formula': f"Q4 {current_year} - Q3 {current_year}"
            })
        
        # Add flows to results
        for flow in flows:
            flow_results.append({
                'company_symbol': company,
                'quarter': flow['quarter'],
                'year': flow['year'],
                'current_value': flow['current_value'],
                'previous_value': flow['previous_value'],
                'flow': flow['flow'],
                'flow_formula': flow['flow_formula']
            })
    
    return flow_results


def main():
    """Main function to calculate retained earnings flow"""
    print("🔄 Calculating Retained Earnings Flow (Quarterly Changes)")
    print("=" * 60)
    
    # Load retained earnings data
    try:
        with open('data/results/retained_earnings_results.json', 'r', encoding='utf-8') as f:
            retained_data = json.load(f)
        print(f"✅ Loaded {len(retained_data)} retained earnings records")
    except FileNotFoundError:
        print("❌ Error: retained_earnings_results.json not found")
        print("Please run the main extraction script first")
        return
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Calculate flows
    print("🔄 Calculating quarterly flows...")
    flow_results = calculate_retained_earnings_flow(retained_data)
    
    if not flow_results:
        print("❌ No flows could be calculated")
        return
    
    # Convert to DataFrame for easier manipulation
    flow_df = pd.DataFrame(flow_results)
    
    # Load ownership data for additional context (prefer JSON, fallback to CSV)
    try:
        try:
            with open('data/ownership/foreign_ownership_data.json', 'r', encoding='utf-8') as f:
                ownership_json = json.load(f)
            ownership_df = pd.DataFrame(ownership_json)
            print(f"✅ Loaded ownership data (JSON) for {len(ownership_df)} companies")
        except FileNotFoundError:
            ownership_df = pd.read_csv('data/ownership/foreign_ownership_data.csv')
            print(f"✅ Loaded ownership data (CSV) for {len(ownership_df)} companies")
        
        # Normalize columns
        if 'symbol' not in ownership_df.columns and 'company_symbol' in ownership_df.columns:
            ownership_df = ownership_df.rename(columns={'company_symbol': 'symbol'})
        
        # Merge with ownership data
        flow_df['company_symbol'] = flow_df['company_symbol'].astype(str)
        ownership_df['symbol'] = ownership_df['symbol'].astype(str)
        
        merged = pd.merge(
            flow_df, 
            ownership_df[['symbol', 'company_name', 'foreign_ownership', 'max_allowed', 'investor_limit']], 
            left_on='company_symbol', 
            right_on='symbol', 
            how='left'
        )
        
        # Calculate reinvested earnings flow (foreign investor portion)
        merged['reinvested_earnings_flow'] = merged.apply(
            lambda row: (
                row['flow'] * (float(str(row['investor_limit']).replace('%', '')) / 100)
                if (pd.notna(row['flow']) and 
                    pd.notna(row['investor_limit']) and 
                    str(row['investor_limit']).replace('%', '').replace('.', '').isdigit() and
                    float(str(row['investor_limit']).replace('%', '')) > 0)
                else 0
            ), 
            axis=1
        )
        
        # Load net profit data for additional calculations
        try:
            with open('data/results/quarterly_net_profit.json', 'r', encoding='utf-8') as f:
                net_profit_data = json.load(f)
            print(f"✅ Loaded net profit data for {len(net_profit_data)} companies")
            
            # Convert net profit data to lookup format
            net_profit_lookup = {}
            for company in net_profit_data:
                symbol = company.get('company_symbol')
                if symbol:
                    net_profit_lookup[symbol] = company
            
            # Prepare raw net profit per quarter (None if missing)
            def get_raw_net_profit(symbol: str, quarter: str, year: int):
                company = net_profit_lookup.get(str(symbol), {})
                qmap = company.get('quarterly_net_profit', {}) if company else {}
                key = f"{quarter} {year}"
                return qmap.get(key, None) if qmap else None

            # Investor limit fraction
            def investor_fraction(val):
                if pd.isna(val):
                    return 0.0
                s = str(val).replace('%', '')
                if not s.replace('.', '').isdigit():
                    return 0.0
                try:
                    return float(s) / 100.0
                except Exception:
                    return 0.0

            # Compute raw net profit and calc/display values
            merged['__raw_net_profit'] = merged.apply(
                lambda row: get_raw_net_profit(row['company_symbol'], row['quarter'], row['year']), axis=1
            )
            merged['__inv_frac'] = merged['investor_limit'].apply(investor_fraction)
            # Numeric for calculations: use 0 when missing
            merged['__net_profit_foreign_investor_calc'] = merged.apply(
                lambda row: (
                    (row['__raw_net_profit'] if row['__raw_net_profit'] is not None else 0) * row['__inv_frac']
                ), axis=1
            )
            # Display column: empty string when raw net profit is missing
            merged['net_profit_foreign_investor'] = merged.apply(
                lambda row: (
                    row['__net_profit_foreign_investor_calc'] if row['__raw_net_profit'] is not None else ''
                ), axis=1
            )
            # Calculate distributed using calc numeric regardless of display
            merged['distributed_profits_foreign_investor'] = merged.apply(
                lambda row: (
                    row['__net_profit_foreign_investor_calc'] - row['reinvested_earnings_flow']
                    if pd.notna(row['reinvested_earnings_flow']) else 0
                ), axis=1
            )
            
            print(f"✅ Added net profit calculations for foreign investors")
            
        except FileNotFoundError:
            print("⚠️ Warning: quarterly_net_profit.json not found, skipping net profit calculations")
            merged['net_profit_foreign_investor'] = 0
            merged['distributed_profits_foreign_investor'] = 0
        except Exception as e:
            print(f"⚠️ Warning: Error processing net profit data: {e}")
            merged['net_profit_foreign_investor'] = 0
            merged['distributed_profits_foreign_investor'] = 0
        
        # Clean up the merged data
        final_results = merged[['company_symbol', 'company_name', 'quarter', 'year', 'current_value', 'previous_value', 'flow', 'flow_formula', 'foreign_ownership', 'max_allowed', 'investor_limit', 'reinvested_earnings_flow', 'net_profit_foreign_investor', 'distributed_profits_foreign_investor']].copy()
        
        print(f"✅ Calculated flows for {len(final_results)} company-quarters")
        print(f"✅ Added foreign investor flow calculations")
        
        # Save to CSV
        csv_path = 'data/results/retained_earnings_flow.csv'
        final_results.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✅ Saved flow data to {csv_path}")
        
        # Save to JSON for debugging
        json_path = 'data/results/retained_earnings_flow.json'
        final_results.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"✅ Saved flow data to {json_path}")

        # New: Save compact per-quarter foreign investor metrics
        compact = final_results[['company_symbol','company_name','quarter','year','reinvested_earnings_flow','net_profit_foreign_investor','distributed_profits_foreign_investor']].copy()
        compact_json_path = 'data/results/foreign_investor_results.json'
        compact.to_json(compact_json_path, orient='records', force_ascii=False, indent=2)
        print(f"✅ Saved foreign investor metrics to {compact_json_path}")
        
        # Display sample results
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
        
    except FileNotFoundError:
        print("⚠️ Warning: ownership data not found, saving basic flow data only")
        # Save basic flow data without ownership calculations
        csv_path = 'data/results/retained_earnings_flow.csv'
        flow_df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✅ Saved basic flow data to {csv_path}")
        
        json_path = 'data/results/retained_earnings_flow.json'
        flow_df.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"✅ Saved basic flow data to {json_path}")
        
    except Exception as e:
        print(f"❌ Error processing ownership data: {e}")
        # Save basic flow data as fallback
        csv_path = 'data/results/retained_earnings_flow.csv'
        flow_df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✅ Saved basic flow data to {csv_path}")
    
    print("\n🎉 Flow calculation completed successfully!") 

if __name__ == "__main__":
    main() 