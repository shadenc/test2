#!/usr/bin/env python3
"""
Flask API for serving evidence screenshots and extraction metadata
"""

from dataclasses import dataclass

from flask import Flask
from flask_cors import CORS
import json
import os
from pathlib import Path
import logging
import subprocess
import sys
from datetime import datetime
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import shutil

# Get environment variables for production
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Path fragments & messages (deduplicated; Sonar / maintainability) ---
SCREENSHOTS_RELPATH = "output/screenshots"
FLOW_CSV_RELPATH = "data/results/retained_earnings_flow.csv"
RESULTS_JSON_RELPATH = "data/results/retained_earnings_results.json"
REINVESTED_CSV_RELPATH = "data/results/reinvested_earnings_results.csv"
QUARTERLY_NET_PROFIT_RELPATH = "data/results/quarterly_net_profit.json"
RUNTIME_STOP_PDFS_FLAG = "data/runtime/stop_pdfs_pipeline.flag"
RUNTIME_PDFS_PROGRESS_JSON = "data/runtime/pdfs_progress.json"
RUNTIME_STOP_NET_FLAG = "data/runtime/stop_net_profit.flag"
RUNTIME_NET_PROGRESS_JSON = "data/runtime/net_profit_progress.json"
SCRIPT_CALCULATE_REINVESTED = "src/calculators/calculate_reinvested_earnings.py"
SCRIPT_GENERATE_SCREENSHOTS = "src/utils/generate_evidence_screenshots.py"
MSG_INTERNAL_ERROR = "Internal server error"
MSG_FILE_NOT_FOUND = "File not found"
MSG_OWNERSHIP_UPDATED_OK = "Ownership data updated successfully"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# Arabic "none" — single literal for Sonar; matches frontend GRID_EMPTY_AR
EMPTY_DISPLAY_AR = "لايوجد"


def format_excel_cell_display(value):
    """Empty / missing → EMPTY_DISPLAY_AR; numeric zero → '0'; else pass-through."""
    if value == "" or value is None:
        return EMPTY_DISPLAY_AR
    if value == 0 or (isinstance(value, str) and value.strip() == "0"):
        return "0"
    return value


def flow_map_from_flow_dataframe(flow_data: pd.DataFrame) -> dict:
    """Symbol → quarter → flow CSV columns (shared by scheduler export and HTTP Excel export)."""
    flow_map: dict = {}
    for _, row in flow_data.iterrows():
        symbol = str(row.get("company_symbol", "")).strip()
        quarter = str(row.get("quarter", "")).strip()
        if not symbol or not quarter:
            continue
        flow_map.setdefault(symbol, {})
        flow_map[symbol][quarter] = {
            "previous_value": row.get("previous_value", ""),
            "current_value": row.get("current_value", ""),
            "flow": row.get("flow", ""),
            "flow_formula": row.get("flow_formula", ""),
            "year": row.get("year", ""),
            "reinvested_earnings_flow": row.get("reinvested_earnings_flow", ""),
            "net_profit_foreign_investor": row.get("net_profit_foreign_investor", ""),
            "distributed_profits_foreign_investor": row.get(
                "distributed_profits_foreign_investor", ""
            ),
        }
    return flow_map


def excel_export_row_from_quarter_data(
    symbol: str,
    ownership_row: dict,
    quarter_data: dict,
    net_profit_display,
    previous_quarter_header: str,
    current_quarter_header: str,
) -> dict:
    """Single dashboard/Excel row (Arabic column headers); used by scheduler and evidence routes."""
    return {
        "رمز الشركة": symbol,
        "الشركة": ownership_row.get("company_name", ""),
        "ملكية جميع المستثمرين الأجانب": ownership_row.get("foreign_ownership", ""),
        "الملكية الحالية": ownership_row.get("max_allowed", ""),
        "ملكية المستثمر الاستراتيجي الأجنبي": ownership_row.get("investor_limit", ""),
        f"الأرباح المبقاة للربع السابق ({previous_quarter_header})": format_excel_cell_display(
            quarter_data.get("previous_value", "")
        ),
        f"الأرباح المبقاة للربع الحالي ({current_quarter_header})": format_excel_cell_display(
            quarter_data.get("current_value", "")
        ),
        "حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)": format_excel_cell_display(
            quarter_data.get("flow", "")
        ),
        "تدفق الأرباح المبقاة للمستثمر الأجنبي": format_excel_cell_display(
            quarter_data.get("reinvested_earnings_flow", "")
        ),
        "صافي الربح": net_profit_display,
        "صافي الربح للمستثمر الأجنبي": format_excel_cell_display(
            quarter_data.get("net_profit_foreign_investor", "")
        ),
        "الأرباح الموزعة للمستثمر الأجنبي": format_excel_cell_display(
            quarter_data.get("distributed_profits_foreign_investor", "")
        ),
    }


EVIDENCE_QUARTER_PARAMS = frozenset({
    "Q4_2024",
    "Q1_2025",
    "Q2_2025",
    "Q3_2025",
    "Q4_2025",
    "Annual_2024",
})


def _safe_quarter_token(quarter: str) -> str:
    return quarter if quarter in EVIDENCE_QUARTER_PARAMS else "other"


def _symbol_len_label(symbol) -> str:
    return str(len(str(symbol)))


def _run_project_script(project_root: Path, script_relpath: str, *, ok_log: str | None = None) -> None:
    """Run a repo Python script from project root (scheduler jobs; deduplicates subprocess.run blocks)."""
    subprocess.run(
        [sys.executable, script_relpath],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    if ok_log:
        logger.info(ok_log)


def _scheduler_quarter_calendar(now: datetime) -> tuple[str, str, int, int]:
    """(current_quarter, previous_quarter, previous_year, current_year)."""
    current_year = now.year
    month = now.month
    if month in (1, 2, 3):
        return "Q1", "Q4", current_year - 1, current_year
    if month in (4, 5, 6):
        return "Q2", "Q1", current_year, current_year
    if month in (7, 8, 9):
        return "Q3", "Q2", current_year, current_year
    return "Q4", "Q3", current_year, current_year


def _scheduler_load_inputs(project_root: Path):
    """Return (ownership_data, flow_df, net_profit_data, csv_path) or None if required files missing."""
    ownership_json_path = project_root / "data/ownership/foreign_ownership_data.json"
    if not ownership_json_path.exists():
        logger.error("[Scheduler] ❌ Ownership data file not found")
        return None
    with open(ownership_json_path, "r", encoding="utf-8") as f:
        ownership_data = json.load(f)

    csv_path = project_root / FLOW_CSV_RELPATH
    if not csv_path.exists():
        logger.error("[Scheduler] ❌ Retained earnings flow data file not found")
        return None
    flow_data = pd.read_csv(csv_path)

    net_profit_data: dict = {}
    net_profit_path = project_root / QUARTERLY_NET_PROFIT_RELPATH
    if net_profit_path.exists():
        with open(net_profit_path, "r", encoding="utf-8") as f:
            net_profit_raw = json.load(f)
            for company in net_profit_raw:
                symbol = company.get("company_symbol")
                if symbol:
                    net_profit_data[symbol] = company

    return ownership_data, flow_data, net_profit_data, csv_path


def _scheduler_merged_export_rows(
    ownership_data,
    flow_map: dict,
    net_profit_data: dict,
    current_quarter: str,
    current_year: int,
    previous_quarter: str,
    previous_year: int,
) -> list:
    merged_data = []
    for ownership_row in ownership_data:
        symbol = str(ownership_row.get("symbol", "")).strip()
        flow_info = flow_map.get(symbol, {})
        net_profit_info = net_profit_data.get(symbol, {})
        quarter_data = flow_info.get(current_quarter, {})

        net_profit_value = EMPTY_DISPLAY_AR
        if net_profit_info and "quarterly_net_profit" in net_profit_info:
            quarter_key = f"{current_quarter} {current_year}"
            qnp = net_profit_info["quarterly_net_profit"]
            if quarter_key in qnp:
                net_profit_value = qnp[quarter_key]

        if current_quarter == "Q1":
            previous_quarter_header = f"{previous_year}Q4"
        else:
            previous_quarter_header = f"{current_year}{previous_quarter}"
        current_quarter_header = f"{current_year}{current_quarter}"

        merged_data.append(
            excel_export_row_from_quarter_data(
                symbol,
                ownership_row,
                quarter_data,
                net_profit_value,
                previous_quarter_header,
                current_quarter_header,
            )
        )
    return merged_data


def _scheduler_archive_outputs(
    project_root: Path,
    output_path,
    csv_path: Path,
    current_year: int,
    current_quarter: str,
) -> None:
    if not output_path:
        logger.error("[Scheduler] ❌ Failed to export Excel file")
        return
    archive_dir = project_root / f"output/archives/{current_year}_{current_quarter}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_excel_name = f"financial_analysis_{current_year}_{current_quarter}.xlsx"
    archive_excel_path = archive_dir / archive_excel_name
    shutil.copy(output_path, archive_excel_path)
    archive_csv_name = f"retained_earnings_flow_{current_year}_{current_quarter}.csv"
    archive_csv_path = archive_dir / archive_csv_name
    shutil.copy(csv_path, archive_csv_path)
    screenshots_archive_dir = archive_dir / "evidence_screenshots"
    screenshots_archive_dir.mkdir(exist_ok=True)
    screenshots_dir = project_root / SCREENSHOTS_RELPATH
    if screenshots_dir.exists():
        quarter_pattern = f"*_{current_quarter.lower()}_{current_year}_evidence.png"
        for screenshot in screenshots_dir.glob(quarter_pattern):
            shutil.copy(screenshot, screenshots_archive_dir / screenshot.name)
    logger.info(f"[Scheduler] ✅ Archived results to {archive_dir}")
    logger.info(f"[Scheduler] ✅ Excel file: {archive_excel_name}")
    logger.info(f"[Scheduler] ✅ CSV file: {archive_csv_name}")
    logger.info("[Scheduler] ✅ Evidence screenshots copied")


def run_quarterly_refresh_and_archive(project_root: Path) -> None:
    """
    Quarterly refresh: recalc, screenshots, export, archive.
    Module-level to keep create_app() cognitive complexity low.
    """
    try:
        logger.info("[Scheduler] Running quarterly refresh and archive...")

        logger.info("[Scheduler] Step 1: Recalculating reinvested earnings...")
        _run_project_script(
            project_root,
            SCRIPT_CALCULATE_REINVESTED,
            ok_log="[Scheduler] ✅ Reinvested earnings calculation completed",
        )

        logger.info("[Scheduler] Step 2: Regenerating evidence screenshots...")
        _run_project_script(
            project_root,
            SCRIPT_GENERATE_SCREENSHOTS,
            ok_log="[Scheduler] ✅ Evidence screenshots regeneration completed",
        )

        logger.info("[Scheduler] Step 3: Exporting dashboard table for each quarter...")

        from src.utils.export_to_excel import ExcelExporter

        exporter = ExcelExporter()

        loaded = _scheduler_load_inputs(project_root)
        if loaded is None:
            return
        ownership_data, flow_data, net_profit_data, csv_path = loaded

        now = datetime.now()
        current_quarter, previous_quarter, previous_year, current_year = _scheduler_quarter_calendar(
            now
        )

        logger.info(f"[Scheduler] Current quarter: {current_quarter} {current_year}")
        logger.info(f"[Scheduler] Previous quarter: {previous_quarter} {previous_year}")

        flow_map = flow_map_from_flow_dataframe(flow_data)
        logger.info(f"[Scheduler] Exporting data for {current_quarter} {current_year}...")

        merged_data = _scheduler_merged_export_rows(
            ownership_data,
            flow_map,
            net_profit_data,
            current_quarter,
            current_year,
            previous_quarter,
            previous_year,
        )
        data = pd.DataFrame(merged_data)
        output_path = exporter.export_dashboard_table(data)
        _scheduler_archive_outputs(
            project_root, output_path, csv_path, current_year, current_quarter
        )

    except Exception as e:
        logger.error(f"[Scheduler] ❌ Error in scheduled refresh: {e}")
        import traceback

        logger.error(f"[Scheduler] Traceback: {traceback.format_exc()}")


def run_daily_ownership_scraper_and_recalc(project_root: Path) -> None:
    """Daily job: ownership JSON + recalc flows."""
    try:
        logger.info("[Scheduler] Running daily ownership update and recalculation...")
        try:
            logger.info("[Scheduler] Step 1: Updating foreign ownership via Tadawul scraper...")
            from src.scrapers.ownership import TadawulOwnershipScraper

            scraper = TadawulOwnershipScraper(base_url="https://www.saudiexchange.sa")
            scraper.scrape_to_files(output_dir=str(project_root / "data/ownership"), debug=False)
            logger.info("[Scheduler] ✅ Ownership data updated")
        except Exception as e:
            logger.error(f"[Scheduler] ❌ Ownership update failed: {e}")

        try:
            logger.info("[Scheduler] Step 2: Recalculating reinvested earnings flows...")
            _run_project_script(
                project_root,
                SCRIPT_CALCULATE_REINVESTED,
                ok_log="[Scheduler] ✅ Recalculation finished",
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"[Scheduler] ❌ Recalculation failed: {e.stderr}")
    except Exception as e:
        logger.error(f"[Scheduler] ❌ Unexpected error in daily ownership job: {e}")


@dataclass(frozen=True)
class EvidenceAppContext:
    """Paths shared by evidence HTTP routes (Flask app.config['EVIDENCE_CTX'])."""

    project_root: Path
    screenshots_dir: Path
    results_file: Path
    metadata_file: Path
    csv_file: Path

    @classmethod
    def from_default_paths(cls) -> "EvidenceAppContext":
        root = Path(__file__).parent.parent.parent.resolve()
        shots = root / SCREENSHOTS_RELPATH
        return cls(
            project_root=root,
            screenshots_dir=shots,
            results_file=root / RESULTS_JSON_RELPATH,
            metadata_file=shots / "evidence_metadata.json",
            csv_file=root / REINVESTED_CSV_RELPATH,
        )


def create_app():
    app = Flask(__name__)
    # Allow CORS from React frontend - supports both localhost and production
    allowed_list = ALLOWED_ORIGINS.split(',') if ALLOWED_ORIGINS != '*' else '*'
    CORS(app, origins=allowed_list)

    # Always resolve paths relative to the project root
    ctx = EvidenceAppContext.from_default_paths()
    app.config["EVIDENCE_CTX"] = ctx

    from src.api.evidence_routes import bp as evidence_bp

    app.register_blueprint(evidence_bp)

    # --- Quarterly Scheduler Setup (jobs call module-level functions to limit create_app complexity) ---
    if os.environ.get('WERKZEUG_RUN_MAIN', 'true') == 'true':
        scheduler = BackgroundScheduler()

        scheduler.add_job(
            run_quarterly_refresh_and_archive,
            'cron',
            month='3,6,9,12',
            day='last',
            hour=23,
            minute=59,
            args=[ctx.project_root],
            id='quarterly_refresh_and_archive',
            replace_existing=True,
        )

        scheduler.add_job(
            run_quarterly_refresh_and_archive,
            'cron',
            hour=2,
            minute=0,
            args=[ctx.project_root],
            id='daily_test_archive',
            replace_existing=True,
        )

        scheduler.add_job(
            run_daily_ownership_scraper_and_recalc,
            'cron',
            hour=3,
            minute=0,
            args=[ctx.project_root],
            id='daily_ownership_and_recalc',
            replace_existing=True,
        )
        
        scheduler.start()
        logger.info("[Scheduler] ✅ Quarterly scheduler started successfully")
        logger.info("[Scheduler] 📅 Will run at end of each quarter (Mar 31, Jun 30, Sep 30, Dec 31)")
        logger.info("[Scheduler] 🧪 Daily test run at 2 AM for development")
        logger.info("[Scheduler] 🗓️ Daily ownership update scheduled at 03:00")

    return app

# Create app instance for Gunicorn
app = create_app()

# Ensure directories exist for production
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
(PROJECT_ROOT / SCREENSHOTS_RELPATH).mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "data/results").mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "data/pdfs").mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    print("Starting Evidence API server...")
    print(f"Screenshots directory: {PROJECT_ROOT / SCREENSHOTS_RELPATH}")
    print("API will be available at: http://localhost:5003")
    
    app.run(debug=True, host='0.0.0.0', port=5003) 