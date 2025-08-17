#!/usr/bin/env python3
"""
Simple Quarterly Export System
Automatically exports dashboard data for each quarter
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Try to import requests for API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests library not available, will use local files only")

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def get_current_quarter():
    """Get current quarter (Q1, Q2, Q3, Q4)"""
    month = datetime.now().month
    if month <= 3:
        return "Q1"
    elif month <= 6:
        return "Q2"
    elif month <= 9:
        return "Q3"
    else:
        return "Q4"

def export_quarterly_dashboard(quarter_filter):
    """Export dashboard data for a specific quarter"""
    try:
        print(f"📊 Exporting dashboard for {quarter_filter}...")
        
        # Get project root
        project_root = Path(__file__).parent
        
        # Load foreign ownership data
        ownership_path = project_root / "data/ownership/foreign_ownership_data.json"
        if not ownership_path.exists():
            print(f"❌ Ownership data not found: {ownership_path}")
            return False
        
        with open(ownership_path, 'r', encoding='utf-8') as f:
            ownership_data = json.load(f)
        
        # Load retained earnings data
        earnings_path = project_root / "data/results/retained_earnings_flow.csv"
        if not earnings_path.exists():
            print(f"❌ Earnings data not found: {earnings_path}")
            return False
        
        earnings_data = pd.read_csv(earnings_path)
        
        # Create flow map exactly like App.js does
        flow_map = {}
        for _, row in earnings_data.iterrows():
            symbol = str(row.get('company_symbol', '')).strip()
            quarter = str(row.get('quarter', '')).strip()
            if symbol and quarter:
                if symbol not in flow_map:
                    flow_map[symbol] = {}
                flow_map[symbol][quarter] = {
                    'previous_value': row.get('previous_value', ''),
                    'current_value': row.get('current_value', ''),
                    'flow': row.get('flow', ''),
                    'flow_formula': row.get('flow_formula', ''),
                    'year': row.get('year', ''),
                    'foreign_investor_flow': row.get('reinvested_earnings_flow', ''),
                    'net_profit_foreign_investor': row.get('net_profit_foreign_investor', ''),
                    'distributed_profits_foreign_investor': row.get('distributed_profits_foreign_investor', '')
                }
        
        # Load net profit data (same as App.js)
        net_profit_data = {}
        try:
            if REQUESTS_AVAILABLE:
                # Try to fetch from API like App.js does
                response = requests.get('http://localhost:5002/api/net-profit')
                if response.status_code == 200:
                    net_profit_data = response.json()
                    print(f"✅ Loaded net profit data from API")
                else:
                    print(f"⚠️ API call failed, trying local file")
                    # Fallback to local file
                    net_profit_path = project_root / "data/results/quarterly_net_profit.json"
                    if net_profit_path.exists():
                        with open(net_profit_path, 'r', encoding='utf-8') as f:
                            net_profit_raw = json.load(f)
                            for company in net_profit_raw:
                                symbol = company.get('company_symbol')
                                if symbol:
                                    net_profit_data[symbol] = company
            else:
                # Use local file if requests not available
                net_profit_path = project_root / "data/results/quarterly_net_profit.json"
                if net_profit_path.exists():
                    with open(net_profit_path, 'r', encoding='utf-8') as f:
                        net_profit_raw = json.load(f)
                        for company in net_profit_raw:
                            symbol = company.get('company_symbol')
                            if symbol:
                                net_profit_data[symbol] = company
        except Exception as e:
            print(f"⚠️ API call failed: {e}, trying local file")
            # Fallback to local file
            net_profit_path = project_root / "data/results/quarterly_net_profit.json"
            if net_profit_path.exists():
                with open(net_profit_path, 'r', encoding='utf-8') as f:
                    net_profit_raw = json.load(f)
                    for company in net_profit_raw:
                        symbol = company.get('company_symbol')
                        if symbol:
                            net_profit_data[symbol] = company
        
        # Create dashboard data exactly like App.js does
        dashboard_data = []
        
        print(f"📊 Processing {len(ownership_data)} companies for {quarter_filter}")
        print(f"📊 Flow map has data for {len(flow_map)} companies")
        print(f"📊 Net profit data has data for {len(net_profit_data)} companies")
        
        for company in ownership_data:
            symbol = company.get('symbol', '')
            company_name = company.get('company_name', '')
            
            # Get earnings data for this quarter
            earnings_info = flow_map.get(symbol, {}).get(quarter_filter, {})
            
            # Get net profit for this quarter (same logic as App.js)
            net_profit = "لايوجد"
            if symbol in net_profit_data:
                company_net_profit = net_profit_data[symbol]
                if company_net_profit and company_net_profit.get('quarterly_net_profit'):
                    # Map quarter filter to 2025 data like App.js does
                    quarter_key = f"{quarter_filter} 2025"
                    value = company_net_profit['quarterly_net_profit'].get(quarter_key)
                    if value is not None:
                        net_profit = value
            
            # Create row with EXACTLY the same structure as App.js dashboard
            row = {
                'رمز الشركة': symbol,
                'الشركة': company_name,
                'ملكية جميع المستثمرين الأجانب': company.get('foreign_ownership', ''),
                'الملكية الحالية': company.get('max_allowed', ''),
                'ملكية المستثمر الاستراتيجي الأجنبي': company.get('investor_limit', ''),
                'الأرباح المبقاة للربع السابق': earnings_info.get('previous_value', 'لايوجد'),
                'الأرباح المبقاة للربع الحالي': earnings_info.get('current_value', 'لايوجد'),
                'حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)': earnings_info.get('flow', 'لايوجد'),
                'تدفق الأرباح المبقاة للمستثمر الأجنبي': earnings_info.get('foreign_investor_flow', 'لايوجد'),
                'صافي الربح': net_profit,
                'صافي الربح للمستثمر الأجنبي': earnings_info.get('net_profit_foreign_investor', 'لايوجد'),
                'الأرباح الموزعة للمستثمر الأجنبي': earnings_info.get('distributed_profits_foreign_investor', 'لايوجد'),
                'الربع': quarter_filter,
                'السنة': earnings_info.get('year', ''),
                'صيغة التدفق': earnings_info.get('flow_formula', '')
            }
            dashboard_data.append(row)
            
            # Debug: Log first few rows
            if len(dashboard_data) <= 3:
                print(f"📊 Sample row {len(dashboard_data)}: {symbol} - {company_name}")
                print(f"   Previous: {earnings_info.get('previous_value', 'لايوجد')}")
                print(f"   Current: {earnings_info.get('current_value', 'لايوجد')}")
                print(f"   Net Profit: {net_profit}")
        
        print(f"📊 Created {len(dashboard_data)} rows for {quarter_filter}")
        
        # Create DataFrame
        df = pd.DataFrame(dashboard_data)
        
        # Export using ExcelExporter
        try:
            from utils.export_to_excel import ExcelExporter
            exporter = ExcelExporter()
            result_path = exporter.export_dashboard_table(df)
            
            if result_path:
                print(f"✅ Dashboard exported: {result_path}")
                
                # Archive to quarterly folder
                current_year = datetime.now().year
                archive_dir = project_root / "output" / "archives" / f"{current_year}_{quarter_filter}"
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                # Use the actual exported filename for archiving
                result_filename = Path(result_path).name
                archive_path = archive_dir / result_filename
                
                import shutil
                shutil.copy2(result_path, archive_path)
                print(f"📁 Archived to: {archive_path}")
                
                return True
            else:
                print("❌ Export failed")
                return False
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            # Fallback: save as CSV
            output_dir = project_root / "output" / "excel"
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / f"dashboard_{quarter_filter}_{datetime.now().year}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"📊 Saved as CSV: {csv_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error exporting dashboard: {e}")
        return False

def auto_export_all_quarters():
    """Automatically export all available quarters"""
    print("🚀 Starting Automatic Quarterly Exports")
    print("=" * 50)
    
    current_year = datetime.now().year
    current_quarter = get_current_quarter()
    
    print(f"📅 Current: {current_year} {current_quarter}")
    
    # Export all quarters up to current
    quarters_to_export = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if q <= current_quarter:
            quarters_to_export.append((q, current_year))
    
    # Add previous year Q4
    quarters_to_export.append(("Q4", current_year - 1))
    
    print(f"📊 Quarters to export: {quarters_to_export}")
    
    success_count = 0
    for quarter, year in quarters_to_export:
        print(f"\n📤 Exporting {year} {quarter}...")
        if export_quarterly_dashboard(quarter):
            success_count += 1
            print(f"✅ {year} {quarter} exported successfully")
        else:
            print(f"❌ {year} {quarter} export failed")
    
    print(f"\n🎉 Export Summary: {success_count}/{len(quarters_to_export)} successful")
    return success_count == len(quarters_to_export)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quarterly Dashboard Export System")
    parser.add_argument("--quarter", help="Export specific quarter (Q1, Q2, Q3, Q4)")
    parser.add_argument("--auto", action="store_true", help="Auto-export all quarters")
    
    args = parser.parse_args()
    
    if args.quarter:
        # Export specific quarter
        success = export_quarterly_dashboard(args.quarter)
        if success:
            print(f"✅ {args.quarter} export completed")
        else:
            print(f"❌ {args.quarter} export failed")
            sys.exit(1)
    elif args.auto:
        # Auto-export all quarters
        success = auto_export_all_quarters()
        if success:
            print("🎉 All quarterly exports completed successfully")
        else:
            print("❌ Some quarterly exports failed")
            sys.exit(1)
    else:
        # Export current quarter
        current_q = get_current_quarter()
        print(f"📊 Exporting current quarter: {current_q}")
        success = export_quarterly_dashboard(current_q)
        if success:
            print(f"✅ {current_q} export completed")
        else:
            print(f"❌ {current_q} export failed")
            sys.exit(1)
