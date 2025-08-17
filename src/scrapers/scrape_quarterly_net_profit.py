#!/usr/bin/env python3
"""
Quarterly Net Profit Scraper for Saudi Exchange
Scrapes quarterly net profit data from company financial information pages
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

# Constants
OUTPUT_DIR = Path("data/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "quarterly_net_profit.json"

def get_company_symbols_from_json():
    """Get company symbols from the existing JSON file."""
    try:
        json_path = Path("frontend/public/foreign_ownership_data.json")
        if not json_path.exists():
            print(f"❌ JSON file not found: {json_path}")
            return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        symbols = [item['symbol'] for item in data if item.get('symbol')]
        print(f"📋 Found {len(symbols)} company symbols from JSON file")
        return symbols
        
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return []

async def setup_stealth_browser():
    """Setup Playwright browser with stealth configuration."""
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=False,  # Set to True for production
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='Asia/Riyadh',
        extra_http_headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    )
    
    # Add stealth scripts
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {},
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' }),
            }),
        });
    """)
    
    return playwright, browser, context

async def navigate_to_company_profile(page: Page, symbol: str) -> bool:
    """Navigate to the company profile page using search."""
    search_url = "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/search/!ut/p/z0/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz8DTxCnA3MDILdzUJDLAyNHI30C7IdFQEEx_vC/"
    
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        print(f"🔍 Navigating to search page for symbol {symbol}")
        
        # Wait for search input and fill symbol
        await page.wait_for_selector("#query-input", timeout=5000)
        await page.click("#query-input")
        await page.fill("#query-input", symbol)
        await page.wait_for_timeout(500)
        
        # Submit search using JavaScript
        await page.evaluate("document.querySelector('div.srchBlueBtn').click()")
        await page.wait_for_timeout(2000)
        
        # Find and click 'Visit Profile' link
        links = await page.query_selector_all("a.pageLink")
        visit_links = []
        
        for link in links:
            text = (await link.text_content() or "").strip().lower()
            if text == "visit profile":
                visit_links.append(link)
        
        if not visit_links:
            print(f"❌ No 'Visit Profile' link found for symbol {symbol}")
            return False
        
        await visit_links[0].click()
        await page.wait_for_load_state('domcontentloaded')
        print(f"✅ Successfully navigated to profile for {symbol}")
        return True
        
    except Exception as e:
        print(f"❌ Navigation failed for {symbol}: {e}")
        return False

async def navigate_to_financial_information(page: Page, symbol: str) -> bool:
    """Navigate to FINANCIAL INFORMATION tab and click Quarterly."""
    try:
        print(f"📊 Looking for FINANCIAL INFORMATION tab for {symbol}...")
        
        # Wait for page to load
        await page.wait_for_timeout(3000)
        
        # Find and click FINANCIAL INFORMATION tab
        tabs = await page.query_selector_all("li")
        financial_info_tab = None
        
        for tab in tabs:
            tab_text = (await tab.text_content() or "").strip()
            tab_id = await tab.get_attribute("id")
            
            # Look for FINANCIAL INFORMATION tab
            if "financial information" in tab_text.lower() or tab_id == "balancesheet":
                financial_info_tab = tab
                print(f"✅ Found FINANCIAL INFORMATION tab: '{tab_text}' (ID: {tab_id})")
                break
        
        if not financial_info_tab:
            print(f"❌ FINANCIAL INFORMATION tab not found for {symbol}")
            return False
        
        # Click FINANCIAL INFORMATION tab
        await financial_info_tab.scroll_into_view_if_needed()
        await financial_info_tab.click()
        await page.wait_for_timeout(2000)
        print(f"✅ Clicked FINANCIAL INFORMATION tab for {symbol}")
        
        # Now look for Quarterly tab - be more specific
        print(f"🔍 Looking for Quarterly tab for {symbol}...")
        quarterly_tab = None
        
        # Wait for content to load
        await page.wait_for_timeout(2000)
        
        # Look for Quarterly tab with more specific criteria
        quarterly_elements = await page.query_selector_all("li, button, a, div")
        
        for element in quarterly_elements:
            try:
                element_text = (await element.text_content() or "").strip().lower()
                element_class = await element.get_attribute("class") or ""
                
                # Look for quarterly tab that's not options trading
                if "quarterly" in element_text and "option" not in element_text and "trading" not in element_text:
                    quarterly_tab = element
                    print(f"✅ Found Quarterly tab: '{element_text}' (class: {element_class})")
                    break
                    
                # Also check for elements with specific quarterly indicators
                if any(term in element_text for term in ["quarterly", "q1", "q2", "q3", "q4"]) and \
                   not any(term in element_text for term in ["option", "trading", "armo"]):
                    quarterly_tab = element
                    print(f"✅ Found Quarterly tab via indicators: '{element_text}' (class: {element_class})")
                    break
                    
            except Exception as e:
                continue
        
        if not quarterly_tab:
            print(f"❌ Quarterly tab not found for {symbol}")
            print("🔍 Trying to find any financial data table...")
            
            # If no quarterly tab, try to find the financial table directly
            tables = await page.query_selector_all("table")
            if tables:
                print(f"📊 Found {len(tables)} tables, proceeding to scrape...")
                return True  # Continue anyway to see what we can scrape
            else:
                print("❌ No tables found either")
                return False
        
        # Click Quarterly tab
        await quarterly_tab.click()
        await page.wait_for_timeout(2000)
        print(f"✅ Clicked Quarterly tab for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to navigate to financial information for {symbol}: {e}")
        return False

async def scrape_quarterly_net_profit(page: Page, symbol: str) -> Optional[Dict]:
    """Scrape quarterly net profit data from the financial table."""
    try:
        print(f"📈 Scraping quarterly net profit data for {symbol}...")
        
        # Wait for table to load
        await page.wait_for_selector("table", timeout=10000)
        await page.wait_for_timeout(2000)
        
        # Find all financial tables
        tables = await page.query_selector_all("table")
        statement_of_income_table = None
        
        print(f"🔍 Found {len(tables)} tables on the page")
        
        # Look specifically for the Statement of Income table
        for i, table in enumerate(tables):
            try:
                table_text = await table.text_content()
                print(f"📊 Table {i} content preview: {table_text[:200]}...")
                
                # Look specifically for Statement of Income with quarterly dates
                if "statement of income" in table_text.lower():
                    # Check if this table has the quarterly dates we want
                    has_quarterly_dates = any(term in table_text.lower() for term in ["2025-06-30", "2025-03-31", "2024-09-30", "2024-06-30"])
                    
                    if has_quarterly_dates:
                        statement_of_income_table = table
                        print(f"✅ Found Statement of Income table {i} with quarterly dates")
                        break
                    else:
                        print(f"📊 Found Statement of Income table {i} but it's annual data")
                        
            except Exception as e:
                print(f"⚠️  Error reading table {i}: {e}")
                continue
        
        # If we didn't find quarterly data, look for any table with the quarterly dates
        if not statement_of_income_table:
            print(f"🔍 Looking for any table with quarterly dates...")
            
            for i, table in enumerate(tables):
                try:
                    table_text = await table.text_content()
                    
                    # Check if this table has the quarterly dates we want
                    has_quarterly_dates = any(term in table_text.lower() for term in ["2025-06-30", "2025-03-31", "2024-09-30", "2024-06-30"])
                    
                    if has_quarterly_dates:
                        statement_of_income_table = table
                        print(f"✅ Found table {i} with quarterly dates")
                        break
                        
                except Exception as e:
                    continue
        
        if not statement_of_income_table:
            print(f"❌ Statement of Income table not found for {symbol}")
            return None
        
        # Get table headers (quarterly dates)
        header_cells = await statement_of_income_table.query_selector_all("thead tr th")
        quarterly_dates = []
        
        print(f"📅 Table headers: {len(header_cells)} cells")
        
        for i, cell in enumerate(header_cells):
            try:
                text = (await cell.text_content() or "").strip()
                print(f"  Header {i}: '{text}'")
                
                # Look for quarterly dates (YYYY-MM-DD format)
                if text and len(text) == 10 and text.count('-') == 2:
                    quarterly_dates.append(text)
                    
            except Exception as e:
                print(f"⚠️  Error reading header {i}: {e}")
                continue
        
        if not quarterly_dates:
            print(f"❌ No quarterly dates found in headers, checking table body...")
            
            # Try to find dates in the first row of table body
            body_rows = await statement_of_income_table.query_selector_all("tbody tr")
            if body_rows:
                first_row_cells = await body_rows[0].query_selector_all("td")
                print(f"📊 First row has {len(first_row_cells)} cells")
                
                for i, cell in enumerate(first_row_cells):
                    try:
                        text = (await cell.text_content() or "").strip()
                        print(f"  Cell {i}: '{text}'")
                        
                        # Look for date format
                        if text and len(text) == 10 and text.count('-') == 2:
                            quarterly_dates.append(text)
                    except Exception as e:
                        print(f"⚠️  Error reading cell {i}: {e}")
                        continue
        
        if not quarterly_dates:
            print(f"❌ No quarterly dates found for {symbol}")
            return None
        
        print(f"📅 Found quarterly dates: {quarterly_dates}")
        
        # Convert dates to quarter labels
        quarters = []
        for date in quarterly_dates:
            try:
                year, month, day = date.split('-')
                month = int(month)
                if month <= 3:
                    quarters.append(f"Q1 {year}")
                elif month <= 6:
                    quarters.append(f"Q2 {year}")
                elif month <= 9:
                    quarters.append(f"Q3 {year}")
                else:
                    quarters.append(f"Q4 {year}")
            except:
                quarters.append(date)
        
        print(f"📅 Converted to quarters: {quarters}")
        
        # Find the Net Profit row in the Statement of Income table
        rows = await statement_of_income_table.query_selector_all("tbody tr")
        net_profit_row = None
        
        print(f"🔍 Looking through {len(rows)} rows for Net Profit...")
        
        for i, row in enumerate(rows):
            try:
                cells = await row.query_selector_all("td")
                if cells:
                    first_cell_text = (await cells[0].text_content() or "").strip().lower()
                    
                    # Look for the exact text from the image
                    if "net profit (loss) before zakat and tax" in first_cell_text:
                        net_profit_row = row
                        print(f"✅ Found Net Profit row {i}: '{first_cell_text}'")
                        break
                        
                    if i < 5:  # Show first few rows for debugging
                        print(f"  Row {i}: '{first_cell_text}'")
                        
            except Exception as e:
                print(f"⚠️  Error reading row {i}: {e}")
                continue
        
        if not net_profit_row:
            print(f"❌ Net Profit row not found for {symbol}")
            return None
        
        # Extract net profit values
        cells = await net_profit_row.query_selector_all("td")
        net_profit_values = {}
        
        print(f"📊 Net Profit row has {len(cells)} cells")
        
        for i, quarter in enumerate(quarters):
            if i + 1 < len(cells):  # +1 because first cell is the label
                cell = cells[i + 1]
                value_text = (await cell.text_content() or "").strip()
                
                if value_text and value_text != "-":
                    # Clean and parse the value
                    clean_value = value_text.replace(",", "").replace(" ", "")
                    try:
                        numeric_value = float(clean_value)
                        net_profit_values[quarter] = numeric_value
                        print(f"💰 {quarter}: {numeric_value:,.0f}")
                    except ValueError:
                        print(f"⚠️  Could not parse value for {quarter}: '{value_text}'")
                        net_profit_values[quarter] = None
                else:
                    net_profit_values[quarter] = None
                    print(f"⚠️  No value for {quarter}")
        
        if not net_profit_values:
            print(f"❌ No net profit values extracted for {symbol}")
            return None
        
        # Create result structure
        result = {
            "company_symbol": symbol,
            "scraped_date": datetime.now().isoformat(),
            "quarterly_net_profit": net_profit_values
        }
        
        print(f"✅ Successfully scraped quarterly net profit data for {symbol}")
        return result
        
    except Exception as e:
        print(f"❌ Error scraping net profit for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def process_company_with_retry(browser: Browser, symbol: str, max_retries: int = 3) -> Optional[Dict]:
    """Process a single company with retry logic."""
    for attempt in range(max_retries):
        try:
            page = await browser.new_page()
            
            # Add random mouse movement for stealth
            await page.mouse.move(random.randint(100, 500), random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Navigate to company profile
            if not await navigate_to_company_profile(page, symbol):
                await page.close()
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying navigation for {symbol} (attempt {attempt + 2}/{max_retries})...")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                return None
            
            # Navigate to financial information
            if not await navigate_to_financial_information(page, symbol):
                await page.close()
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying financial info navigation for {symbol} (attempt {attempt + 2}/{max_retries})...")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                return None
            
            # Scrape net profit data
            result = await scrape_quarterly_net_profit(page, symbol)
            await page.close()
            
            if result:
                return result
            elif attempt < max_retries - 1:
                print(f"🔄 Retrying scraping for {symbol} (attempt {attempt + 2}/{max_retries})...")
                await asyncio.sleep(random.uniform(2, 5))
                
        except Exception as e:
            print(f"❌ Error processing {symbol} (attempt {attempt + 1}): {e}")
            await page.close()
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
    
    return None

async def scrape_all_companies_net_profit():
    """Scrape quarterly net profit data for all companies."""
    # Get company symbols
    companies = get_company_symbols_from_json()
    
    if not companies:
        print("❌ No company symbols found. Please ensure foreign_ownership_data.json exists.")
        return
    
    print(f"📋 Found {len(companies)} companies to process")
    
    # Setup browser
    playwright, browser, context = await setup_stealth_browser()
    
    try:
        results = []
        success_count = 0
        failed_count = 0
        
        for i, symbol in enumerate(companies, 1):
            print(f"\n{'='*60}")
            print(f"📊 Processing {symbol} ({i}/{len(companies)})")
            print(f"{'='*60}")
            
            result = await process_company_with_retry(browser, symbol)
            
            if result:
                results.append(result)
                success_count += 1
                print(f"✅ Successfully processed {symbol}")
            else:
                failed_count += 1
                print(f"❌ Failed to process {symbol}")
            
            # Stop after 10 companies
            if i >= 10:
                print(f"\n🛑 Stopping after 10 companies as requested")
                break
            
            # Add delay between companies
            if i < len(companies) and i < 10:
                delay = random.uniform(3, 7)
                print(f"⏳ Waiting {delay:.1f} seconds before next company...")
                await asyncio.sleep(delay)
        
        # Save results
        if results:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {OUTPUT_FILE}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Success Rate: {(success_count/(success_count+failed_count)*100):.1f}%")
        print(f"💾 Data saved to: {OUTPUT_FILE}")
        
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    print("🚀 Starting Quarterly Net Profit Scraper...")
    print("📊 This will scrape quarterly net profit data from Saudi Exchange")
    print("⏳ Please ensure you have a stable internet connection")
    
    # Run the scraper
    asyncio.run(scrape_all_companies_net_profit())
