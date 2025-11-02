import asyncio
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import random

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

# Constants
BASE_URL = "https://www.saudiexchange.sa/wps/portal/saudiexchange/companies/company-profile-main/"
PDF_DIR = Path("data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Statement type priorities (most preferred first)
STATEMENT_PRIORITIES = [
    "annual",
    "quarterly", 
    "interim",
    "financial",
    "report"
]

# Set the target year here. By default, use the current year, but you can set it manually if needed.
target_year = datetime.now().year  # Change this to e.g. 2024 to process 2024 and 2023 Q4

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
        # Optional limit for testing
        try:
            limit = int(os.environ.get("LIMIT_COMPANIES", "0"))
            if limit > 0:
                symbols = symbols[:limit]
        except Exception:
            pass
        print(f"📋 Found {len(symbols)} company symbols from JSON file")
        return symbols
        
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return []

async def setup_stealth_browser():
    """Setup Playwright browser with stealth configuration from download_pdf_playwright.py."""
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=False,  # Start with non-headless for testing
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
        accept_downloads=True,
        locale='en-US',
        timezone_id='America/New_York',
        permissions=['geolocation'],
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
    
    # Add stealth scripts from download_pdf_playwright.py
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
    """Navigate to the company profile page using the working approach from download_annual_reports.py."""
    search_url = "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/search/!ut/p/z0/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz8DTxCnA3MDILdzUJDLAyNHI30C7IdFQEEx_vC/"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
    print(f"Navigated to search page for symbol {symbol}")
    try:
        # Focus the input, fill the symbol, and submit search
        await page.wait_for_selector("#query-input", timeout=5000)
        await page.click("#query-input")
        await page.fill("#query-input", symbol)
        await page.wait_for_timeout(500)
        # Use only JS click to submit
        await page.evaluate("document.querySelector('div.srchBlueBtn').click()")
        await page.wait_for_timeout(2000)
        # Print all a.pageLink elements for debugging
        links = await page.query_selector_all("a.pageLink")
        print('--- <a.pageLink> elements on the page ---')
        for i, link in enumerate(links):
            text = (await link.text_content() or '').strip()
            href = await link.get_attribute('href')
            print(f'{i}: text="{text}", href="{href}"')
        print('--- end of <a.pageLink> debug ---')
        # Find and click the 'Visit Profile' button by text
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
        print(f"✅ Clicked 'Visit Profile' for symbol {symbol}")
        return True
    except Exception as e:
        print(f"❌ Search failed for {symbol}: {e}")
        return False

async def get_all_financial_reports(page: Page, symbol: str):
    """Find all available financial report PDFs (Annual, Q1-Q4) and their years, filtered for target_year and Q4 of previous year."""
    if not await navigate_to_company_profile(page, symbol):
        return []
    print("On company profile page, waiting for content...")
    await page.wait_for_timeout(3000)
    tabs = await page.query_selector_all("li")
    try:
        target_text = "financial statements and reports"
        for tab in tabs:
            tab_text = (await tab.text_content() or "").strip().lower()
            if target_text in tab_text:
                await tab.scroll_into_view_if_needed()
                await tab.click()
                print(f"✅ Clicked tab: {tab_text}")
                break
        else:
            print("❌ 'Financial Statements and Reports' tab not found by substring.")
            return []
    except PlaywrightTimeoutError:
        print("❌ Timeout while trying to find financial tab.")
        return []
    try:
        # Wait for any table to appear first
        await page.wait_for_selector("table", timeout=10000)
        print("Table found, waiting for content to load...")
        
        # Wait a bit more for dynamic content
        await page.wait_for_timeout(2000)
        
        # Try to find the financial statements table
        table_selector = "table:has-text('Annual')"
        try:
            await page.wait_for_selector(table_selector, timeout=5000)
            print("Financial statements table loaded with 'Annual' text.")
        except:
            # If that fails, look for any table with financial data
            tables = await page.query_selector_all("table")
            print(f"Found {len(tables)} tables on the page")
            
            for i, table in enumerate(tables):
                table_text = await table.text_content()
                if any(term in table_text.lower() for term in ["annual", "quarterly", "financial", "report"]):
                    print(f"Table {i} appears to contain financial data")
                    break
            else:
                print("No table with financial data found")
                return []
    except Exception as e:
        print(f"Could not find financial statements table: {e}")
        return []
    header_cells = await page.query_selector_all("table thead tr th")
    years = []
    for cell in header_cells:
        text = (await cell.text_content()).strip()
        if text.isdigit():
            years.append(int(text))
    if not years:
        print("No years found in table header.")
        return []
    rows = await page.query_selector_all("table tbody tr")
    print(f"Found {len(rows)} rows in financial statements table")
    
    # Debug: Print all row contents to understand the structure
    print("--- Table rows debug ---")
    for i, row in enumerate(rows):
        cells = await row.query_selector_all("td")
        row_text = []
        for j, cell in enumerate(cells):
            cell_text = (await cell.text_content() or "").strip()
            row_text.append(f"cell{j}: '{cell_text}'")
        print(f"Row {i}: {row_text}")
    print("--- End table debug ---")
    
    statement_types = ["annual", "q1", "q2", "q3", "q4"]
    found_reports = []
    
    for stype in statement_types:
        row = None
        # Search through all rows for this statement type
        for r in rows:
            first_cell = await r.query_selector("td")
            if first_cell:
                cell_text = (await first_cell.text_content() or "").strip().lower()
                # More flexible matching
                if stype in cell_text or any(term in cell_text for term in ["report", "statement"]):
                    row = r
                    print(f"Found row for {stype}: '{cell_text}'")
                    break
        
        if not row:
            print(f"No '{stype}' row found in table.")
            continue
            
        cells = await row.query_selector_all("td")
        print(f"Row for {stype} has {len(cells)} cells")
        
        for i, year in enumerate(years):
            cell_index = i + 1  # offset by 1 for the label cell
            if cell_index >= len(cells):
                continue
            cell = cells[cell_index]
            pdf_link = await cell.query_selector("a[href$='.pdf']")
            if pdf_link:
                pdf_url = await pdf_link.get_attribute("href")
                if pdf_url:
                    normalized_stype = stype.lower().strip()
                    print(f"🎯 Found {normalized_stype.upper()} PDF URL for {symbol} {year}: {pdf_url}")
                    found_reports.append((normalized_stype, year, pdf_url))
    # Updated filter: Q1, Q2, Q3 of current year and Annual of previous year
    filtered_reports = []
    for stype, year, pdf_url in found_reports:
        if year == target_year and stype in ["q1", "q2", "q3"]:
            filtered_reports.append((stype, year, pdf_url))
        elif year == target_year - 1 and stype == "annual":
            filtered_reports.append((stype, year, pdf_url))
    print(f"[DEBUG] Will download for {symbol}: {[f'{stype}_{year}' for stype, year, _ in filtered_reports]}")
    return filtered_reports

async def download_pdf_with_stealth(page: Page, pdf_url: str, symbol: str, year: int, statement_type: str) -> bool:
    """Download PDF using the working stealth approach, generalized for statement type."""
    try:
        # Respect stop flag before starting any new download
        stop_flag_env = os.environ.get("STOP_FLAG_FILE", "data/runtime/stop_pdfs_pipeline.flag")
        stop_flag_path = Path(stop_flag_env)
        if stop_flag_path.exists():
            print("🛑 Stop requested. Skipping new PDF download request.")
            return False
        filename = f"{symbol}_{statement_type}_{year}.pdf"
        pdf_path = PDF_DIR / filename
        if pdf_path.exists():
            print(f"⚠️  {filename} already exists, skipping...")
            return True
        print(f"📥 Downloading {filename}...")
        if not pdf_url.startswith("http"):
            pdf_url = f"https://www.saudiexchange.sa{pdf_url}"
        response = await page.goto(pdf_url, wait_until='networkidle')
        # Check again immediately after navigation in case stop was hit during navigation
        if stop_flag_path.exists():
            print("🛑 Stop requested after navigation. Aborting download save.")
            return False
        content_type = response.headers.get('content-type', '')
        if 'pdf' in content_type.lower():
            print(f"✅ Successfully accessed PDF for {symbol}")
            pdf_content = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch(window.location.href);
                        const arrayBuffer = await response.arrayBuffer();
                        return Array.from(new Uint8Array(arrayBuffer));
                    } catch (error) {
                        console.error('Error fetching PDF:', error);
                        return null;
                    }
                }
            """)
            if pdf_content:
                with open(pdf_path, 'wb') as f:
                    f.write(bytes(pdf_content))
                print(f"✅ Downloaded {filename} ({len(pdf_content)} bytes)")
                return True
            else:
                print(f"❌ Failed to get PDF content for {symbol}")
                return False
        else:
            print(f"❌ Did not get PDF content for {symbol} (Content-Type: {content_type})")
            return False
    except Exception as e:
        print(f"❌ Download error for {symbol}: {e}")
        return False

async def process_company_with_retry(browser: Browser, symbol: str, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            # Abort early if stop requested
            stop_flag_env = os.environ.get("STOP_FLAG_FILE", "data/runtime/stop_pdfs_pipeline.flag")
            if Path(stop_flag_env).exists():
                print("🛑 Stop requested. Aborting company processing.")
                return False
            page = await browser.new_page()
            await page.mouse.move(random.randint(100, 500), random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            reports = await get_all_financial_reports(page, symbol)
            if not reports:
                await page.close()
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying {symbol} (attempt {attempt + 2}/{max_retries})...")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                return False
            all_success = True
            for stype, year, pdf_url in reports:
                # Check stop flag before starting each report download
                if Path(stop_flag_env).exists():
                    print("🛑 Stop requested. Halting further report downloads for this company.")
                    all_success = False
                    break
                success = await download_pdf_with_stealth(page, pdf_url, symbol, year, stype)
                if not success:
                    all_success = False
            await page.close()
            if all_success:
                return True
            elif attempt < max_retries - 1:
                print(f"🔄 Retrying {symbol} (attempt {attempt + 2}/{max_retries})...")
                await asyncio.sleep(random.uniform(2, 5))
        except Exception as e:
            print(f"❌ Error processing {symbol} (attempt {attempt + 1}): {e}")
            await page.close()
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
    return False

async def download_all_financial_statements():
    """Download the most recent financial statements for all companies."""
    # Get company symbols from JSON file
    companies = get_company_symbols_from_json()
    # companies = ["2030"]  # Test with a single company
    if not companies:
        print("❌ No company symbols found. Please run the ownership scraper first.")
        return

    print(f"📋 Found {len(companies)} companies to process")
    
    # Setup browser with stealth configuration
    playwright, browser, context = await setup_stealth_browser()
    
    try:
        # progress reporting
        progress_path = Path(os.environ.get("PROGRESS_FILE", "data/runtime/pdfs_progress.json"))
        processed = 0
        success_count = 0
        failed_count = 0
        
        # Stop flag support
        stop_flag = Path(os.environ.get("STOP_FLAG_FILE", "data/runtime/stop_pdfs_pipeline.flag"))
        stop_flag.parent.mkdir(parents=True, exist_ok=True)

        for i, symbol in enumerate(companies, 1):
            if stop_flag.exists():
                print("🛑 Stop requested. Ending PDF pipeline early.")
                break
            print(f"\n{'='*50}")
            print(f"📊 Processing {symbol} ({i}/{len(companies)})")
            print(f"{'='*50}")
            
            success = await process_company_with_retry(browser, symbol)
            
            if success:
                success_count += 1
                print(f"✅ Successfully processed {symbol}")
            else:
                failed_count += 1
                print(f"❌ Failed to process {symbol}")
            processed += 1
            # write progress
            try:
                progress_path.parent.mkdir(parents=True, exist_ok=True)
                with open(progress_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "status": "running",
                        "processed": processed,
                        "success": success_count,
                        "failed": failed_count,
                        "current_symbol": symbol
                    }, f, ensure_ascii=False)
            except Exception:
                pass
            
            # Add delay between companies
            if i < len(companies):
                # If stop requested, skip waiting and break immediately
                if stop_flag.exists():
                    print("🛑 Stop requested. Skipping wait and ending now.")
                    break
                delay = random.uniform(3, 7)
                print(f"⏳ Waiting {delay:.1f} seconds before next company...")
                await asyncio.sleep(delay)
        
        # Summary
        print(f"\n{'='*50}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*50}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        total = success_count + failed_count
        rate = (success_count/total*100) if total > 0 else 0.0
        print(f"📈 Success Rate: {rate:.1f}%")
        # mark done
        try:
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "status": "completed",
                    "processed": processed,
                    "success": success_count,
                    "failed": failed_count
                }, f, ensure_ascii=False)
        except Exception:
            pass
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    # Uncomment to download all reports for all companies
    asyncio.run(download_all_financial_statements())
    
    # Comment out the test function when running all companies
    # async def test_single_company():
    #     # Test with the company we know has data
    #     symbol = "2030"
    #     print(f"🧪 Testing with {symbol} to verify new filtering...")
    #     
    #     playwright, browser, context = await setup_stealth_browser()
    #     try:
    #         success = await process_company_with_retry(browser, symbol)
    #         print(f"Test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    #     finally:
    #             await browser.close()
    #             await playwright.stop()
    # 
    # # Run the test
    # asyncio.run(test_single_company()) 