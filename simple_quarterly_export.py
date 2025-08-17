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
        
        # Create earnings map by symbol and quarter
        earnings_map = {}
        for _, row in earnings_data.iterrows():
            symbol = str(row.get('company_symbol', '')).strip()
            quarter = str(row.get('quarter', '')).strip()
            if symbol and quarter:
                if symbol not in earnings_map:
                    earnings_map[symbol] = {}
                earnings_map[symbol][quarter] = {
                    'retained_earnings': row.get('current_value', 'لا يوجد'),
                    'reinvested_earnings': row.get('reinvested_earnings_flow', 'لا يوجد')
                }
        
        # Load net profit data
        net_profit_path = project_root / "data/results/quarterly_net_profit.json"
        net_profit_data = {}
        if net_profit_path.exists():
            with open(net_profit_path, 'r', encoding='utf-8') as f:
                net_profit_raw = json.load(f)
                for company in net_profit_raw:
                    symbol = company.get('company_symbol')
                    if symbol:
                        net_profit_data[symbol] = company
        
        # Create dashboard data
        dashboard_data = []
        for company in ownership_data:
            symbol = company.get('symbol', '')
            company_name = company.get('company_name', '')
            
            # Get earnings data for this quarter
            earnings_info = earnings_map.get(symbol, {}).get(quarter_filter, {})
            
            # Get net profit for this quarter
            net_profit = "لا يوجد"
            if symbol in net_profit_data:
                quarterly_data = net_profit_data[symbol].get('quarterly_net_profit', {})
                quarter_key = f"{quarter_filter} 2025"
                if quarter_key in quarterly_data:
                    net_profit = quarterly_data[quarter_key]
            
            # Create row
            row = {
                'رمز الشركة': symbol,
                'الشركة': company_name,
                'ملكية جميع المستثمرين الأجانب': company.get('foreign_ownership', ''),
                'الملكية الحالية': company.get('max_allowed', ''),
                'ملكية المستثمر الاستراتيجي الأجنبي': company.get('investor_limit', ''),
                'الأرباح المبقاة': earnings_info.get('retained_earnings', 'لا يوجد'),
                'الأرباح المعاد استثمارها': earnings_info.get('reinvested_earnings', 'لا يوجد'),
                'صافي الربح': net_profit,
                'الربع': quarter_filter
            }
            dashboard_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(dashboard_data)
        
        # Export to Excel
        output_dir = project_root / "output" / "excel"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        current_year = datetime.now().year
        filename = f"dashboard_{quarter_filter}_{current_year}.xlsx"
        output_path = output_dir / filename
        
        # Export using ExcelExporter
        try:
            from utils.export_to_excel import ExcelExporter
            exporter = ExcelExporter()
            result_path = exporter.export_dashboard_table(df)
            
            if result_path:
                print(f"✅ Dashboard exported: {result_path}")
                
                # Archive to quarterly folder
                archive_dir = project_root / "output" / "archives" / f"{current_year}_{quarter_filter}"
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                archive_path = archive_dir / filename
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
            csv_path = output_path.with_suffix('.csv')
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
