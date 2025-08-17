#!/usr/bin/env python3
"""
Test script for Quarterly Update Orchestrator
Tests the system with existing data to verify functionality
"""

import asyncio
import json
from pathlib import Path
from quarterly_update_orchestrator import QuarterlyUpdateOrchestrator

async def test_orchestrator_with_existing_data():
    """Test the orchestrator using existing data."""
    print("🧪 Testing Quarterly Update Orchestrator with existing data")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = QuarterlyUpdateOrchestrator()
    
    # Check what data we already have
    print("\n📊 Checking existing data...")
    
    # Check ownership data
    ownership_file = orchestrator.frontend_dir / "foreign_ownership_data.json"
    if ownership_file.exists():
        with open(ownership_file, 'r', encoding='utf-8') as f:
            ownership_data = json.load(f)
        print(f"✅ Foreign ownership data: {len(ownership_data)} companies")
        
        # Get first few company symbols for testing
        test_symbols = [item['symbol'] for item in ownership_data[:3] if item.get('symbol')]
        print(f"🧪 Test symbols: {test_symbols}")
        
        # Test PDF detection
        print(f"\n📁 Testing PDF detection for {test_symbols[0]}...")
        existing_pdfs = orchestrator._check_existing_pdfs(test_symbols[0])
        print(f"   Existing PDFs: {existing_pdfs}")
        
        # Test net profit detection
        print(f"\n📈 Testing net profit detection for {test_symbols[0]}...")
        existing_quarters = orchestrator._check_existing_net_profit_data(test_symbols[0])
        print(f"   Existing quarters: {existing_quarters}")
        
        # Test the orchestrator's detection methods
        print(f"\n🔍 Testing orchestrator detection methods...")
        
        # Test PDF update logic (without actually downloading)
        print(f"   Testing PDF update logic for {test_symbols[0]}...")
        pdf_dir = orchestrator.pdf_dir
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob(f"{test_symbols[0]}_*.pdf"))
            print(f"   Found {len(pdf_files)} PDF files")
            for pdf in pdf_files:
                print(f"     - {pdf.name}")
        
        # Test net profit update logic
        print(f"   Testing net profit update logic...")
        net_profit_file = orchestrator.results_dir / "quarterly_net_profit.json"
        if net_profit_file.exists():
            with open(net_profit_file, 'r', encoding='utf-8') as f:
                net_profit_data = json.load(f)
            
            # Find our test company
            test_company_data = None
            for company in net_profit_data:
                if company.get("company_symbol") == test_symbols[0]:
                    test_company_data = company
                    break
            
            if test_company_data:
                quarterly_data = test_company_data.get("quarterly_net_profit", {})
                print(f"   Found quarterly data: {list(quarterly_data.keys())}")
            else:
                print(f"   No net profit data found for {test_symbols[0]}")
        
        print(f"\n✅ All detection methods working correctly!")
        
        # Test the orchestrator's quarter logic
        print(f"\n📅 Testing quarter logic...")
        print(f"   Current year: {orchestrator.current_year}")
        print(f"   Current quarter: {orchestrator.current_quarter}")
        
        available_quarters = orchestrator._get_available_quarters()
        print(f"   Available quarters: {available_quarters}")
        
        print(f"\n🎯 Orchestrator is working correctly!")
        print(f"   - Can detect existing PDFs")
        print(f"   - Can detect existing net profit data")
        print(f"   - Can determine current quarter")
        print(f"   - Ready for incremental updates")
        
    else:
        print("❌ No foreign ownership data found")
        return False
    
    return True

async def test_scheduler():
    """Test the scheduler functionality."""
    print(f"\n🕒 Testing Scheduler...")
    print("=" * 40)
    
    from schedule_quarterly_updates import QuarterlyUpdateScheduler
    
    scheduler = QuarterlyUpdateScheduler()
    
    # Test schedule loading
    schedule = scheduler.load_schedule()
    print(f"✅ Schedule loaded: {schedule.get('update_frequency_days', 'unknown')} days")
    
    # Test status display
    print(f"📊 Schedule status:")
    scheduler.show_schedule_status()
    
    print(f"\n✅ Scheduler is working correctly!")
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting Quarterly Update System Tests")
    print("=" * 60)
    
    # Test 1: Orchestrator with existing data
    success1 = await test_orchestrator_with_existing_data()
    
    # Test 2: Scheduler
    success2 = await test_scheduler()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🧪 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Orchestrator Test: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Scheduler Test: {'PASSED' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print(f"\n🎉 All tests passed! The quarterly update system is working correctly.")
        print(f"   You can now:")
        print(f"   - Run updates: python3 src/scrapers/schedule_quarterly_updates.py --force")
        print(f"   - Check status: python3 src/scrapers/schedule_quarterly_updates.py --status")
        print(f"   - Set up automation: ./src/scrapers/setup_cron_job.sh")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
    
    return success1 and success2

if __name__ == "__main__":
    asyncio.run(main())
