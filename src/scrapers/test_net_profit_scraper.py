#!/usr/bin/env python3
"""
Test script for Quarterly Net Profit Scraper
Tests with a single company to verify the scraping logic works
"""

import asyncio
import json
from pathlib import Path

from scrape_quarterly_net_profit import (
    setup_stealth_browser,
    navigate_to_company_profile,
    navigate_to_financial_information,
    scrape_quarterly_net_profit
)

async def test_single_company():
    """Test the scraper with a single company."""
    # Test with company 2222 (Aramco) instead of 2030
    test_symbol = "2222"
    
    print(f"🧪 Testing Net Profit Scraper with company: {test_symbol}")
    print("=" * 60)
    
    # Setup browser
    playwright, browser, context = await setup_stealth_browser()
    
    try:
        page = await browser.new_page()
        
        print(f"🔍 Step 1: Navigating to company profile for {test_symbol}")
        if not await navigate_to_company_profile(page, test_symbol):
            print("❌ Failed to navigate to company profile")
            return
        
        print(f"📊 Step 2: Navigating to FINANCIAL INFORMATION tab")
        if not await navigate_to_financial_information(page, test_symbol):
            print("❌ Failed to navigate to financial information")
            return
        
        print(f"📈 Step 3: Scraping quarterly net profit data")
        result = await scrape_quarterly_net_profit(page, test_symbol)
        
        if result:
            print("\n✅ SUCCESS! Scraped data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Save test result
            test_output = Path("data/results/test_net_profit.json")
            test_output.parent.mkdir(parents=True, exist_ok=True)
            
            with open(test_output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Test result saved to: {test_output}")
        else:
            print("❌ Failed to scrape net profit data")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    print("🧪 Starting Net Profit Scraper Test...")
    print("📊 This will test with a single company to verify the scraping logic")
    print("⏳ Please ensure you have a stable internet connection")
    
    # Run the test
    asyncio.run(test_single_company())
