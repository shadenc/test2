
#!/usr/bin/env python3
"""
Quarterly Net Profit Scraper for Saudi Exchange
Scrapes quarterly net profit data from company financial information pages
"""

import asyncio
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

# Constants
OUTPUT_DIR = Path("data/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "quarterly_net_profit.json"
SEARCH_INPUT_SELECTOR = "#query-input"


async def _async_read_json_file(path: Path):
    def _read():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return await asyncio.to_thread(_read)


async def _async_write_json_file(path: Path, obj) -> None:
    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    await asyncio.to_thread(_write)


_QUARTERLY_TABLE_DATE_HINTS = (
    "2025-06-30",
    "2025-03-31",
    "2024-09-30",
    "2024-06-30",
)


def _table_text_has_quarterly_date_hint(table_text: str) -> bool:
    lower = table_text.lower()
    return any(h in lower for h in _QUARTERLY_TABLE_DATE_HINTS)


async def _find_statement_of_income_with_quarterly_dates(tables):
    for i, table in enumerate(tables):
        try:
            table_text = await table.text_content()
            print(f"📊 Table {i} content preview: {table_text[:200]}...")
            if "statement of income" not in table_text.lower():
                continue
            if _table_text_has_quarterly_date_hint(table_text):
                print(f"✅ Found Statement of Income table {i} with quarterly dates")
                return table
            print(f"📊 Found Statement of Income table {i} but it's annual data")
        except Exception as e:
            print(f"⚠️  Error reading table {i}: {e}")
    return None


async def _first_table_with_quarterly_date_hints(tables):
    for i, table in enumerate(tables):
        try:
            table_text = await table.text_content()
            if _table_text_has_quarterly_date_hint(table_text):
                print(f"✅ Found table {i} with quarterly dates")
                return table
        except Exception:
            continue
    return None


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
            import os
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
        await page.wait_for_selector(SEARCH_INPUT_SELECTOR, timeout=5000)
        await page.click(SEARCH_INPUT_SELECTOR)
        await page.fill(SEARCH_INPUT_SELECTOR, symbol)
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


async def _click_financial_information_tab(page: Page, symbol: str) -> bool:
    await page.wait_for_timeout(3000)
    tabs = await page.query_selector_all("li")
    for tab in tabs:
        tab_text = (await tab.text_content() or "").strip()
        tab_id = await tab.get_attribute("id")
        if "financial information" in tab_text.lower() or tab_id == "balancesheet":
            print(f"✅ Found FINANCIAL INFORMATION tab: '{tab_text}' (ID: {tab_id})")
            await tab.scroll_into_view_if_needed()
            await tab.click()
            await page.wait_for_timeout(2000)
            print(f"✅ Clicked FINANCIAL INFORMATION tab for {symbol}")
            return True
    print(f"❌ FINANCIAL INFORMATION tab not found for {symbol}")
    return False


def _text_looks_like_quarterly_tab(text_lower: str) -> bool:
    if "quarterly" in text_lower and "option" not in text_lower and "trading" not in text_lower:
        return True
    if any(t in text_lower for t in ["quarterly", "q1", "q2", "q3", "q4"]) and not any(
        t in text_lower for t in ["option", "trading", "armo"]
    ):
        return True
    return False


async def _find_quarterly_tab_element(page: Page):
    await page.wait_for_timeout(2000)
    for element in await page.query_selector_all("li, button, a, div"):
        try:
            element_text = (await element.text_content() or "").strip().lower()
            element_class = await element.get_attribute("class") or ""
            if _text_looks_like_quarterly_tab(element_text):
                print(f"✅ Found Quarterly tab: '{element_text}' (class: {element_class})")
                return element
        except Exception:
            continue
    return None


def _is_iso_date_cell(text: str) -> bool:
    return bool(text and len(text) == 10 and text.count("-") == 2)


async def _collect_quarterly_dates_from_header_cells(header_cells) -> List[str]:
    quarterly_dates: List[str] = []
    for i, cell in enumerate(header_cells):
        try:
            text = (await cell.text_content() or "").strip()
            print(f"  Header {i}: '{text}'")
            if _is_iso_date_cell(text):
                quarterly_dates.append(text)
        except Exception as e:
            print(f"⚠️  Error reading header {i}: {e}")
    return quarterly_dates


async def _collect_quarterly_dates_from_first_body_row(statement_of_income_table) -> List[str]:
    body_rows = await statement_of_income_table.query_selector_all("tbody tr")
    if not body_rows:
        return []
    first_row_cells = await body_rows[0].query_selector_all("td")
    print(f"📊 First row has {len(first_row_cells)} cells")
    quarterly_dates: List[str] = []
    for i, cell in enumerate(first_row_cells):
        try:
            text = (await cell.text_content() or "").strip()
            print(f"  Cell {i}: '{text}'")
            if _is_iso_date_cell(text):
                quarterly_dates.append(text)
        except Exception as e:
            print(f"⚠️  Error reading cell {i}: {e}")
    return quarterly_dates


def _quarter_labels_from_iso_dates(quarterly_dates: List[str]) -> List[str]:
    quarters: List[str] = []
    for date in quarterly_dates:
        try:
            year, month, _ = date.split("-")
            month = int(month)
            if month <= 3:
                quarters.append(f"Q1 {year}")
            elif month <= 6:
                quarters.append(f"Q2 {year}")
            elif month <= 9:
                quarters.append(f"Q3 {year}")
            else:
                quarters.append(f"Q4 {year}")
        except (ValueError, AttributeError):
            quarters.append(date)
    return quarters


async def _find_net_profit_row_in_statement(rows, symbol: str):
    print(f"🔍 Looking through {len(rows)} rows for Net Profit...")
    for i, row in enumerate(rows):
        try:
            cells = await row.query_selector_all("td")
            if not cells:
                continue
            first_cell_text = (await cells[0].text_content() or "").strip().lower()
            if "net profit (loss) before zakat and tax" in first_cell_text:
                print(f"✅ Found Net Profit row {i}: '{first_cell_text}'")
                return row
            if i < 5:
                print(f"  Row {i}: '{first_cell_text}'")
        except Exception as e:
            print(f"⚠️  Error reading row {i}: {e}")
    print(f"❌ Net Profit row not found for {symbol}")
    return None


async def _net_profit_values_for_quarters(
    net_profit_row, quarters: List[str]
) -> Dict[str, Optional[float]]:
    cells = await net_profit_row.query_selector_all("td")
    net_profit_values: Dict[str, Optional[float]] = {}
    print(f"📊 Net Profit row has {len(cells)} cells")
    for i, quarter in enumerate(quarters):
        if i + 1 >= len(cells):
            continue
        cell = cells[i + 1]
        value_text = (await cell.text_content() or "").strip()
        if not value_text or value_text == "-":
            net_profit_values[quarter] = None
            print(f"⚠️  No value for {quarter}")
            continue
        clean_value = value_text.replace(",", "").replace(" ", "")
        try:
            numeric_value = float(clean_value)
            net_profit_values[quarter] = numeric_value
            print(f"💰 {quarter}: {numeric_value:,.0f}")
        except ValueError:
            print(f"⚠️  Could not parse value for {quarter}: '{value_text}'")
            net_profit_values[quarter] = None
    return net_profit_values


async def navigate_to_financial_information(page: Page, symbol: str) -> bool:
    """Navigate to FINANCIAL INFORMATION tab and click Quarterly."""
    try:
        print(f"📊 Looking for FINANCIAL INFORMATION tab for {symbol}...")
        if not await _click_financial_information_tab(page, symbol):
            return False
        print(f"🔍 Looking for Quarterly tab for {symbol}...")
        quarterly_tab = await _find_quarterly_tab_element(page)
        if not quarterly_tab:
            print(f"❌ Quarterly tab not found for {symbol}")
            print("🔍 Trying to find any financial data table...")
            tables = await page.query_selector_all("table")
            if tables:
                print(f"📊 Found {len(tables)} tables, proceeding to scrape...")
                return True
            print("❌ No tables found either")
            return False
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

        await page.wait_for_selector("table", timeout=10000)
        await page.wait_for_timeout(2000)

        tables = await page.query_selector_all("table")
        print(f"🔍 Found {len(tables)} tables on the page")
        statement_of_income_table = await _find_statement_of_income_with_quarterly_dates(tables)
        if not statement_of_income_table:
            print("🔍 Looking for any table with quarterly dates...")
            statement_of_income_table = await _first_table_with_quarterly_date_hints(tables)

        if not statement_of_income_table:
            print(f"❌ Statement of Income table not found for {symbol}")
            return None

        header_cells = await statement_of_income_table.query_selector_all("thead tr th")
        print(f"📅 Table headers: {len(header_cells)} cells")
        quarterly_dates = await _collect_quarterly_dates_from_header_cells(header_cells)

        if not quarterly_dates:
            print("❌ No quarterly dates found in headers, checking table body...")
            quarterly_dates = await _collect_quarterly_dates_from_first_body_row(
                statement_of_income_table
            )

        if not quarterly_dates:
            print(f"❌ No quarterly dates found for {symbol}")
            return None

        print(f"📅 Found quarterly dates: {quarterly_dates}")
        quarters = _quarter_labels_from_iso_dates(quarterly_dates)
        print(f"📅 Converted to quarters: {quarters}")

        rows = await statement_of_income_table.query_selector_all("tbody tr")
        net_profit_row = await _find_net_profit_row_in_statement(rows, symbol)
        if not net_profit_row:
            return None

        net_profit_values = await _net_profit_values_for_quarters(net_profit_row, quarters)
        if not net_profit_values:
            print(f"❌ No net profit values extracted for {symbol}")
            return None

        result = {
            "company_symbol": symbol,
            "scraped_date": datetime.now().isoformat(),
            "quarterly_net_profit": net_profit_values,
        }
        print(f"✅ Successfully scraped quarterly net profit data for {symbol}")
        return result

    except Exception as e:
        print(f"❌ Error scraping net profit for {symbol}: {e}")
        import traceback

        traceback.print_exc()
        return None


def _net_profit_should_retry(attempt: int, max_retries: int) -> bool:
    return attempt < max_retries - 1


async def _safe_close_net_profit_page(page: Optional[Page]) -> None:
    if page is not None:
        await page.close()


def _log_net_profit_retry_attempt(
    symbol: str, attempt: int, max_retries: int, phase: str
) -> None:
    """phase: profile | financial | scrape"""
    nxt = attempt + 2
    if phase == "profile":
        print(f"🔄 Retrying navigation for {symbol} (attempt {nxt}/{max_retries})...")
        return
    if phase == "financial":
        print(
            f"🔄 Retrying financial info navigation for {symbol} "
            f"(attempt {nxt}/{max_retries})..."
        )
        return
    print(f"🔄 Retrying scraping for {symbol} (attempt {nxt}/{max_retries})...")


async def _run_one_net_profit_scrape_attempt(
    browser: Browser, symbol: str
) -> Tuple[Optional[Dict], str]:
    """
    One browser page lifecycle: navigate, scrape. Returns (data, phase).
    phase is 'ok' if data is not None; otherwise profile | financial | scrape.
    """
    page: Optional[Page] = await browser.new_page()
    try:
        await page.mouse.move(random.randint(100, 500), random.randint(100, 300))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        if not await navigate_to_company_profile(page, symbol):
            return None, "profile"
        if not await navigate_to_financial_information(page, symbol):
            return None, "financial"
        data = await scrape_quarterly_net_profit(page, symbol)
        if data:
            return data, "ok"
        return None, "scrape"
    finally:
        await _safe_close_net_profit_page(page)


async def process_company_with_retry(browser: Browser, symbol: str, max_retries: int = 3) -> Optional[Dict]:
    """Process a single company with retry logic."""
    for attempt in range(max_retries):
        try:
            result, phase = await _run_one_net_profit_scrape_attempt(browser, symbol)
            if result is not None:
                return result
            if not _net_profit_should_retry(attempt, max_retries):
                return None
            _log_net_profit_retry_attempt(symbol, attempt, max_retries, phase)
            await asyncio.sleep(random.uniform(2, 5))
        except Exception as e:
            print(f"❌ Error processing {symbol} (attempt {attempt + 1}): {e}")
            if not _net_profit_should_retry(attempt, max_retries):
                return None
            await asyncio.sleep(random.uniform(2, 5))
    return None


def _net_profit_progress_and_stop_paths() -> tuple[Path, Path]:
    progress_path = Path(os.environ.get("PROGRESS_FILE", "data/runtime/net_profit_progress.json"))
    stop_flag = Path(os.environ.get("STOP_FLAG_FILE", "data/runtime/stop_net_profit.flag"))
    stop_flag.parent.mkdir(parents=True, exist_ok=True)
    return progress_path, stop_flag


def _env_limit_companies() -> int:
    try:
        return int(os.environ.get("LIMIT_COMPANIES", "0"))
    except Exception:
        return 0


async def _load_existing_net_profit_map() -> Dict[str, Dict]:
    existing_map: Dict[str, Dict] = {}
    if not OUTPUT_FILE.exists():
        return existing_map
    try:
        existing_list = await _async_read_json_file(OUTPUT_FILE)
        for item in existing_list:
            sym = str(item.get("company_symbol", "")).strip()
            if sym:
                existing_map[sym] = item
        print(f"🔄 Loaded existing net profit data for {len(existing_map)} companies to merge")
    except Exception as e:
        print(f"⚠️ Failed to load existing net profit file, starting fresh merge: {e}")
    return existing_map


async def _write_net_profit_progress(
    progress_path: Path,
    *,
    status: str,
    processed: int,
    success_count: int,
    failed_count: int,
    current_symbol: Optional[str] = None,
) -> None:
    payload: Dict = {
        "status": status,
        "processed": processed,
        "success": success_count,
        "failed": failed_count,
    }
    if current_symbol is not None:
        payload["current_symbol"] = current_symbol
    try:
        await _async_write_json_file(progress_path, payload)
    except Exception:
        pass


async def _scrape_one_company_and_merge(
    browser: Browser, symbol: str, index: int, total: int, existing_map: Dict[str, Dict]
) -> bool:
    print(f"\n{'='*60}")
    print(f"📊 Processing {symbol} ({index}/{total})")
    print(f"{'='*60}")
    result = await process_company_with_retry(browser, symbol)
    if not result:
        print(f"❌ Failed to process {symbol}")
        return False
    print(f"✅ Successfully processed {symbol}")
    existing_map[str(symbol)] = result
    try:
        await _async_write_json_file(OUTPUT_FILE, list(existing_map.values()))
        print(f"💾 Incrementally updated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to write incremental update: {e}")
    return True


def _print_net_profit_summary(success_count: int, failed_count: int) -> None:
    print(f"\n{'='*60}")
    print("📊 SCRAPING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    denom = success_count + failed_count
    rate = (success_count / denom * 100) if denom > 0 else 0.0
    print(f"📈 Success Rate: {rate:.1f}%")
    print(f"💾 Data saved to: {OUTPUT_FILE}")


async def scrape_all_companies_net_profit():
    """Scrape quarterly net profit data for all companies."""
    companies = get_company_symbols_from_json()
    if not companies:
        print("❌ No company symbols found. Please ensure foreign_ownership_data.json exists.")
        return

    print(f"📋 Found {len(companies)} companies to process")
    playwright, browser, _ = await setup_stealth_browser()
    try:
        existing_map = await _load_existing_net_profit_map()
        progress_path, stop_flag = _net_profit_progress_and_stop_paths()
        success_count = 0
        failed_count = 0
        processed = 0
        limit = _env_limit_companies()
        n = len(companies)

        for i, symbol in enumerate(companies, 1):
            if stop_flag.exists():
                print("🛑 Stop requested. Ending net profit scraping early.")
                break
            ok = await _scrape_one_company_and_merge(browser, symbol, i, n, existing_map)
            success_count += 1 if ok else 0
            failed_count += 0 if ok else 1
            processed += 1
            await _write_net_profit_progress(
                progress_path,
                status="running",
                processed=processed,
                success_count=success_count,
                failed_count=failed_count,
                current_symbol=symbol,
            )
            if limit and i >= limit:
                print(f"\n🛑 Stopping after {limit} companies as requested")
                break
            if i < n and i < 10:
                delay = random.uniform(3, 7)
                print(f"⏳ Waiting {delay:.1f} seconds before next company...")
                await asyncio.sleep(delay)

        _print_net_profit_summary(success_count, failed_count)
        await _write_net_profit_progress(
            progress_path,
            status="completed",
            processed=processed,
            success_count=success_count,
            failed_count=failed_count,
        )
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    print("🚀 Starting Quarterly Net Profit Scraper...")
    print("📊 This will scrape quarterly net profit data from Saudi Exchange")
    print("⏳ Please ensure you have a stable internet connection")
    
    # Run the scraper
    asyncio.run(scrape_all_companies_net_profit())
