#!/usr/bin/env python3
"""
Test script to verify date-based quarterly detection logic
"""

from datetime import datetime, date
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.append(str(Path('src')))

from utils.quarterly_archiver import QuarterlyArchiver

def test_date_parsing():
    """Test the date parsing logic."""
    print("🧪 Testing Date-Based Quarterly Detection")
    print("=" * 50)
    
    archiver = QuarterlyArchiver()
    
    # Test current date
    today = date.today()
    current_quarter = archiver.get_current_quarter()
    print(f"📅 Today: {today}")
    print(f"🎯 Current Quarter: {current_quarter}")
    print(f"📊 Month: {today.month}")
    print()
    
    # Test quarter logic for different months
    print("📋 Quarter Logic Test:")
    test_dates = [
        date(2025, 1, 15),   # January
        date(2025, 3, 31),   # March
        date(2025, 4, 1),    # April
        date(2025, 6, 30),   # June
        date(2025, 7, 1),    # July
        date(2025, 9, 30),   # September
        date(2025, 10, 1),   # October
        date(2025, 12, 31),  # December
    ]
    
    for test_date in test_dates:
        quarter = archiver.get_quarter_from_date(test_date)
        print(f"  {test_date.strftime('%B %d, %Y')}: {quarter}")
    
    print()
    
    # Test filename parsing
    print("📁 Filename Date Parsing Test:")
    test_filenames = [
        "financial_analysis_20250115_120000.xlsx",  # Q1
        "financial_analysis_20250401_120000.xlsx",  # Q2
        "financial_analysis_20250817_120000.xlsx",  # Q3 (current)
        "financial_analysis_20251001_120000.xlsx",  # Q4
    ]
    
    for filename in test_filenames:
        try:
            # Extract date from filename (format: YYYYMMDD_HHMMSS)
            date_part = filename.replace("financial_analysis_", "").split("_")[0]
            if len(date_part) >= 8:
                date_str = date_part[:8]
                file_date = datetime.strptime(date_str, "%Y%m%d").date()
                quarter = archiver.get_quarter_from_date(file_date)
                year = file_date.year
                print(f"  {filename}: {quarter} {year}")
            else:
                print(f"  {filename}: Invalid date format")
        except Exception as e:
            print(f"  {filename}: Error - {e}")
    
    print()
    
    # Test actual files in output/excel
    print("📊 Actual Files Analysis:")
    excel_dir = Path("output/excel")
    if excel_dir.exists():
        excel_files = list(excel_dir.glob("financial_analysis_*.xlsx"))
        print(f"  Found {len(excel_files)} financial analysis files")
        
        # Analyze first few files
        for i, excel_file in enumerate(excel_files[:5], 1):
            try:
                filename = excel_file.stem
                date_part = filename.replace("financial_analysis_", "")
                
                if len(date_part) >= 8:
                    date_str = date_part[:8]
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    quarter = archiver.get_quarter_from_date(file_date)
                    year = file_date.year
                    print(f"  {i}. {excel_file.name}: {quarter} {year}")
                else:
                    print(f"  {i}. {excel_file.name}: Invalid date format")
            except Exception as e:
                print(f"  {i}. {excel_file.name}: Error - {e}")
    else:
        print("  No output/excel directory found")
    
    print()
    print("✅ Date logic test completed!")

if __name__ == "__main__":
    test_date_parsing()
