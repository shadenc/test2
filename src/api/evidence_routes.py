"""HTTP routes for evidence API (extracted from create_app for Sonar cognitive complexity)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Blueprint, current_app, jsonify, make_response, request, send_file

from src.api.evidence_api import (
    EMPTY_DISPLAY_AR,
    FLOW_CSV_RELPATH,
    MIME_XLSX,
    MSG_INTERNAL_ERROR,
    MSG_OWNERSHIP_UPDATED_OK,
    QUARTERLY_NET_PROFIT_RELPATH,
    RUNTIME_NET_PROGRESS_JSON,
    RUNTIME_PDFS_PROGRESS_JSON,
    RUNTIME_STOP_NET_FLAG,
    RUNTIME_STOP_PDFS_FLAG,
    SCRIPT_CALCULATE_REINVESTED,
    SCRIPT_GENERATE_SCREENSHOTS,
    format_excel_cell_display,
    logger,
    run_quarterly_refresh_and_archive,
    _safe_quarter_token,
    _symbol_len_label,
)

bp = Blueprint("evidence_api_routes", __name__)


def _ctx():
    return current_app.config["EVIDENCE_CTX"]


def _quarter_evidence_globs(company_symbol: str, quarter: str) -> tuple[str, str | None]:
    """Primary glob under screenshots dir; optional Q1→annual-2024 secondary glob."""
    s = company_symbol
    annual_2024 = f"{s}_*_annual_2024_evidence.png"
    known: dict[str, tuple[str, str | None]] = {
        "Q4_2024": (f"{s}_*_q4_2024_evidence.png", None),
        "Q1_2025": (f"{s}_*_q1_2025_evidence.png", annual_2024),
        "Q2_2025": (f"{s}_*_q2_2025_evidence.png", None),
        "Q3_2025": (f"{s}_*_q3_2025_evidence.png", None),
        "Q4_2025": (f"{s}_*_q4_2025_evidence.png", None),
        "Annual_2024": (annual_2024, None),
    }
    return known.get(quarter, (f"{s}_*_evidence.png", None))


def _list_evidence_screenshots_for_quarter(
    screenshots_dir: Path, company_symbol: str, quarter: str
) -> list[Path]:
    """Resolve screenshot paths: quarter-specific glob, Q1 annual fallback, then any evidence."""
    primary, q1_fallback = _quarter_evidence_globs(company_symbol, quarter)
    files = list(screenshots_dir.glob(primary))
    if quarter == "Q1_2025" and not files and q1_fallback is not None:
        logger.info(
            "No Q1 2025 screenshot; trying annual 2024 fallback (symbol_len=%s)",
            _symbol_len_label(company_symbol),
        )
        files = list(screenshots_dir.glob(q1_fallback))
    if not files:
        files = list(screenshots_dir.glob(f"{company_symbol}_*_evidence.png"))
    return files


@bp.route('/api/evidence/<company_symbol>.png', methods=['GET'])
def get_evidence_screenshot(company_symbol):
    """
    Serve evidence screenshot for a specific company and quarter
    """
    try:
        # Get quarter parameter from query string
        quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025

        screenshot_files = _list_evidence_screenshots_for_quarter(
            _ctx().screenshots_dir, company_symbol, quarter
        )

        if not screenshot_files:
            return jsonify({"error": "Evidence screenshot not found"}), 404
        
        # Use the first available screenshot
        screenshot_path = screenshot_files[0]
        logger.info(
            "Serving evidence screenshot file=%s quarter=%s symbol_len=%s",
            screenshot_path.name,
            _safe_quarter_token(quarter),
            _symbol_len_label(company_symbol),
        )

        return send_file(str(screenshot_path), mimetype='image/png')

    except Exception as e:
        logger.error(
            "Error serving screenshot (symbol_len=%s): %s",
            _symbol_len_label(company_symbol),
            type(e).__name__,
        )
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/extractions', methods=['GET'])
def get_extractions():
    """
    Get all extraction results with evidence information
    """
    try:
        # Load extraction results
        with open(_ctx().results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Load evidence metadata if available
        evidence_metadata = {}
        if _ctx().metadata_file.exists():
            with open(_ctx().metadata_file, 'r', encoding='utf-8') as f:
                evidence_data = json.load(f)
                for item in evidence_data:
                    evidence_metadata[item['company_symbol']] = {
                        'has_evidence': True,
                        'screenshot_path': item['screenshot_path']
                    }
        
        # Add evidence information to results
        for result in results:
            company_symbol = result['company_symbol']
            if company_symbol in evidence_metadata:
                result['evidence'] = evidence_metadata[company_symbol]
            else:
                result['evidence'] = {'has_evidence': False}
        
        return jsonify({
            'extractions': results,
            'total': len(results),
            'successful': len([r for r in results if r['success']])
        })
        
    except Exception as e:
        logger.error(f"Error serving extractions: {e}")
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/extractions/<company_symbol>', methods=['GET'])
def get_extraction_by_company(company_symbol):
    """
    Get extraction result for a specific company and quarter
    """
    try:
        # Get quarter parameter from query string
        quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025

        # Load extraction results
        with open(_ctx().results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)

        company_result = next(
            (r for r in results if r['company_symbol'] == company_symbol),
            None,
        )

        if not company_result:
            return jsonify({"error": "Company not found"}), 404

        screenshot_files = _list_evidence_screenshots_for_quarter(
            _ctx().screenshots_dir, company_symbol, quarter
        )
        has_evidence = len(screenshot_files) > 0

        # Add evidence information
        company_result['evidence'] = {
            'has_evidence': has_evidence,
            'screenshot_path': screenshot_files[0].name if has_evidence else None,
            'requested_quarter': quarter,
            'found_screenshots': [f.name for f in screenshot_files]
        }
        
        return jsonify(company_result)
        
    except Exception as e:
        logger.error(
            "Error serving extraction (symbol_len=%s): %s",
            _symbol_len_label(company_symbol),
            type(e).__name__,
        )
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/evidence/metadata', methods=['GET'])
def get_evidence_metadata():
    """
    Get metadata about all available evidence screenshots
    """
    try:
        if not _ctx().metadata_file.exists():
            return jsonify({"evidence_screenshots": []})
        
        with open(_ctx().metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return jsonify({
            "evidence_screenshots": metadata,
            "total_screenshots": len(metadata)
        })
        
    except Exception as e:
        logger.error(f"Error serving evidence metadata: {e}")
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/evidence/<company_symbol>', methods=['GET'])
def get_evidence(company_symbol):
    """
    Get evidence data for a specific company
    """
    try:
        # Load extraction results
        with open(_ctx().results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Find the specific company
        company_result = None
        for result in results:
            if result['company_symbol'] == company_symbol:
                company_result = result
                break
        
        if not company_result:
            return jsonify({"error": "Company not found"}), 404
        
        # Load evidence metadata
        evidence_data = None
        if _ctx().metadata_file.exists():
            with open(_ctx().metadata_file, 'r', encoding='utf-8') as f:
                evidence_list = json.load(f)
                for item in evidence_list:
                    if item['company_symbol'] == company_symbol:
                        evidence_data = item
                        break
        
        # Prepare response
        response = {
            'company_symbol': company_symbol,
            'extracted_value': company_result.get('numeric_value'),
            'method': company_result.get('method', 'regex'),
            'confidence': company_result.get('confidence', 'medium'),
            'screenshot_url': None,
            'context': company_result.get('raw_match', '')
        }
        
        # Add screenshot URL if available
        if evidence_data:
            response['screenshot_url'] = f"/api/evidence/{company_symbol}.png"
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(
            "Error serving evidence (symbol_len=%s): %s",
            _symbol_len_label(company_symbol),
            type(e).__name__,
        )
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/retained_earnings_flow.csv', methods=['GET'])
def get_retained_earnings_flow_csv():
    """Get retained earnings flow data as CSV."""
    try:
        csv_path = _ctx().project_root / FLOW_CSV_RELPATH
        if not csv_path.exists():
            return "No data available", 404
            
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=retained_earnings_flow.csv'
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        print(f"Error serving CSV: {e}")
        return f"Error: {str(e)}", 500

@bp.route('/api/reinvested_earnings_results.csv', methods=['GET'])
def get_reinvested_earnings_results():
    """
    Serve reinvested earnings results as CSV (legacy endpoint)
    """
    try:
        if not _ctx().csv_file.exists():
            logger.warning(f"CSV file not found: {_ctx().csv_file}")
            return jsonify({"error": "Data not available"}), 404
        
        return send_file(
            str(_ctx().csv_file), 
            mimetype='text/csv',
            as_attachment=True,
            download_name='reinvested_earnings_results.csv'
        )
        
    except Exception as e:
        logger.error(f"Error serving CSV: {e}")
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/refresh', methods=['POST'])
def refresh_data():
    """
    Refreshes the data by updating ownership data, recalculating reinvested earnings,
    and regenerating evidence screenshots. Mirrors the 3 AM scheduled job.
    """
    try:
        logger.info("Starting data refresh (ownership + recalc + screenshots)...")
        
        # 0. Update ownership data (scraper) via subprocess to avoid browser/runtime conflicts
        try:
            logger.info("Updating foreign ownership via Tadawul scraper (subprocess)...")
            scraper_script = _ctx().project_root / "src/scrapers/ownership.py"
            result = subprocess.run(
                [sys.executable, str(scraper_script)],
                check=True,
                capture_output=True,
                text=True,
                timeout=600
            )
            logger.info(MSG_OWNERSHIP_UPDATED_OK)
            if result.stdout:
                logger.debug(result.stdout)
            if result.stderr:
                logger.debug(result.stderr)
        except subprocess.TimeoutExpired:
            logger.warning("Ownership update timed out; continuing with previous ownership data")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Ownership update failed; continuing with previous data: {e.stderr}")
        except Exception as e:
            logger.warning(f"Ownership update failed or skipped: {e}")
        
        # 1. Recalculate reinvested earnings (this is the main step)
        logger.info("Recalculating reinvested earnings...")
        try:
            subprocess.run([sys.executable, SCRIPT_CALCULATE_REINVESTED], 
                         check=True, capture_output=True, text=True)
            logger.info("Reinvested earnings calculation completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error in reinvested earnings calculation: {e}")
            return jsonify({
                "status": "error", 
                "message": f"Failed to recalculate earnings: {e.stderr}"
            }), 500
        
        # 2. Regenerate evidence screenshots (optional)
        logger.info("Regenerating evidence screenshots...")
        try:
            subprocess.run([sys.executable, SCRIPT_GENERATE_SCREENSHOTS], 
                         check=True, capture_output=True, text=True)
            logger.info("Evidence screenshots regeneration completed successfully")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Evidence screenshots regeneration failed: {e}")
            # Don't fail the entire refresh for this step

        logger.info("Data refresh completed successfully")
        return jsonify({
            "status": "success", 
            "message": "Data refreshed successfully (ownership + recalculation + screenshots)."
        }), 200
        
    except Exception as e:
        logger.error(f"Error during data refresh: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Refresh failed: {str(e)}"
        }), 500

@bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "screenshots_dir": str(_ctx().screenshots_dir),
        "screenshots_available": _ctx().screenshots_dir.exists()
    })

def _run_pdfs_pipeline_task(project_root: Path, downloader: Path, extractor: Path):
    try:
        # Clear any stale stop flag from previous runs to avoid auto-stop
        try:
            stop_flag_file = project_root / RUNTIME_STOP_PDFS_FLAG
            if stop_flag_file.exists():
                stop_flag_file.unlink()
        except Exception:
            pass
        # mark progress running
        try:
            progress_path = project_root / RUNTIME_PDFS_PROGRESS_JSON
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump({"status": "running", "processed": 0}, f)
        except Exception:
            pass
        logger.info("[Pipeline] Starting hybrid downloader...")
        env = os.environ.copy()
        env.setdefault('STOP_FLAG_FILE', str(project_root / RUNTIME_STOP_PDFS_FLAG))
        env.setdefault('PROGRESS_FILE', str(project_root / RUNTIME_PDFS_PROGRESS_JSON))
        subprocess.run([sys.executable, str(downloader)], cwd=str(project_root), check=True, text=True, env=env)
    except subprocess.CalledProcessError as e:
        logger.error(f"[Pipeline] Downloader failed: {e}")
        return
    # If a stop was requested, do not run extractor/calc/screenshots here.
    try:
        stop_flag_file = project_root / RUNTIME_STOP_PDFS_FLAG
        if stop_flag_file.exists():
            logger.info("[Pipeline] Stop flag detected after downloader. Skipping extractor/calc/screenshots (finalization thread handles them).")
            # Mark completed and return
            try:
                progress_path = project_root / RUNTIME_PDFS_PROGRESS_JSON
                with open(progress_path, 'w', encoding='utf-8') as f:
                    json.dump({"status": "completed"}, f)
            except Exception:
                pass
            return
    except Exception:
        pass
    try:
        logger.info("[Pipeline] Starting retained earnings extractor...")
        subprocess.run([sys.executable, str(extractor)], cwd=str(project_root), check=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[Pipeline] Extractor failed: {e}")
        return
    try:
        logger.info("[Pipeline] Recalculating reinvested earnings...")
        calc = project_root / SCRIPT_CALCULATE_REINVESTED
        subprocess.run([sys.executable, str(calc)], cwd=str(project_root), check=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[Pipeline] Calculation failed: {e}")
        return
    try:
        logger.info("[Pipeline] Regenerating evidence screenshots...")
        shots = project_root / SCRIPT_GENERATE_SCREENSHOTS
        subprocess.run([sys.executable, str(shots)], cwd=str(project_root), check=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.warning(f"[Pipeline] Screenshot regeneration failed: {e}")
    # mark completed
    try:
        progress_path = project_root / RUNTIME_PDFS_PROGRESS_JSON
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump({"status": "completed"}, f)
    except Exception:
        pass
    # Ensure stop flag is cleared for next runs
    try:
        stop_flag_file = project_root / RUNTIME_STOP_PDFS_FLAG
        if stop_flag_file.exists():
            stop_flag_file.unlink()
    except Exception:
        pass
    logger.info("[Pipeline] ✅ Pipeline completed (download → extract → calculate → screenshots)")

@bp.route('/api/run_pdfs_pipeline', methods=['POST'])
def run_pdfs_pipeline():
    """
    Long-running: download latest PDFs (hybrid_financial_downloader.py), then extract retained earnings
    (extract_retained_earnings_all_pdfs.py). Runs in background; returns immediately.
    """
    try:
        project_root = _ctx().project_root
        downloader = project_root / 'src/scrapers/hybrid_financial_downloader.py'
        extractor = project_root / 'src/extractors/extract_retained_earnings_all_pdfs.py'
        if not downloader.exists() or not extractor.exists():
            return jsonify({"status": "error", "message": "Pipeline scripts not found"}), 404

        # Run both steps in a background thread with safe args (handles spaces in paths)
        threading.Thread(target=_run_pdfs_pipeline_task, args=(project_root, downloader, extractor), daemon=True).start()
        return jsonify({"status": "accepted", "message": "PDF pipeline started in background"}), 202
    except Exception as e:
        logger.error(f"Failed to start PDFs pipeline: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/run_net_profit_scrape', methods=['POST'])
def run_net_profit_scrape():
    """
    Long-running: scrape quarterly net profit for companies, then recalc flows.
    Runs in background; returns immediately.
    """
    try:
        project_root = _ctx().project_root
        scraper = project_root / 'src/scrapers/scrape_quarterly_net_profit.py'
        if not scraper.exists():
            return jsonify({"status": "error", "message": "Net profit scraper not found"}), 404

        def _run_net_profit_task():
            try:
                logger.info("[NetProfit] Starting scraper...")
                # Clear any stale stop flag
                try:
                    net_stop_flag = project_root / RUNTIME_STOP_NET_FLAG
                    if net_stop_flag.exists():
                        net_stop_flag.unlink()
                except Exception:
                    pass
                # Initialize progress file as running
                try:
                    net_progress = project_root / RUNTIME_NET_PROGRESS_JSON
                    net_progress.parent.mkdir(parents=True, exist_ok=True)
                    with open(net_progress, 'w', encoding='utf-8') as f:
                        json.dump({"status": "running", "processed": 0}, f)
                except Exception:
                    pass
                env = os.environ.copy()
                env.setdefault('STOP_FLAG_FILE', str(project_root / RUNTIME_STOP_NET_FLAG))
                env.setdefault('PROGRESS_FILE', str(project_root / RUNTIME_NET_PROGRESS_JSON))
                subprocess.run([sys.executable, str(scraper)], cwd=str(project_root), check=True, text=True, env=env)
            except subprocess.CalledProcessError as e:
                logger.error(f"[NetProfit] Scraper failed: {e}")
                return
            try:
                logger.info("[NetProfit] Recalculating flows after net profit update...")
                calc = project_root / SCRIPT_CALCULATE_REINVESTED
                subprocess.run([sys.executable, str(calc)], cwd=str(project_root), check=True, text=True)
                logger.info("[NetProfit] ✅ Completed")
            except subprocess.CalledProcessError as e:
                logger.error(f"[NetProfit] Recalculation failed: {e}")
            finally:
                # Ensure stop flag cleared at end
                try:
                    net_stop_flag = project_root / RUNTIME_STOP_NET_FLAG
                    if net_stop_flag.exists():
                        net_stop_flag.unlink()
                except Exception:
                    pass

        threading.Thread(target=_run_net_profit_task, daemon=True).start()
        return jsonify({"status": "accepted", "message": "Net profit scraping started in background"}), 202
    except Exception as e:
        logger.error(f"Failed to start net profit scraper: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/pdfs/status', methods=['GET'])
def pdfs_status():
    progress_file = _ctx().project_root / RUNTIME_PDFS_PROGRESS_JSON
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify({"status": "idle"})

@bp.route('/api/net_profit/status', methods=['GET'])
def net_profit_status():
    progress_file = _ctx().project_root / RUNTIME_NET_PROGRESS_JSON
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify({"status": "idle"})

@bp.route('/api/pdfs/stop', methods=['POST'])
def stop_pdfs_pipeline():
    flag = _ctx().project_root / RUNTIME_STOP_PDFS_FLAG
    try:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text('stop', encoding='utf-8')
        # Immediately kick off finalize: extractor -> calc -> screenshots in separate thread
        def _finalize_after_stop():
            try:
                # Mark status as finalizing for the UI
                try:
                    progress_path = _ctx().project_root / RUNTIME_PDFS_PROGRESS_JSON
                    with open(progress_path, 'w', encoding='utf-8') as f:
                        json.dump({"status": "finalizing"}, f)
                except Exception:
                    pass
                extractor = _ctx().project_root / 'src/extractors/extract_retained_earnings_all_pdfs.py'
                calc = _ctx().project_root / SCRIPT_CALCULATE_REINVESTED
                shots = _ctx().project_root / SCRIPT_GENERATE_SCREENSHOTS
                logger.info("[Pipeline] Stop requested: running extractor on downloaded PDFs...")
                env = os.environ.copy()
                env.setdefault('STOP_FLAG_FILE', str(flag))
                subprocess.run([sys.executable, str(extractor)], cwd=str(_ctx().project_root), check=True, text=True, env=env)
                # If partial results exist, promote them to main results
                try:
                    results_dir = _ctx().project_root / 'data/results'
                    partial = results_dir / 'retained_earnings_results.partial.json'
                    main = results_dir / 'retained_earnings_results.json'
                    if partial.exists():
                        shutil.copy(partial, main)
                        logger.info("[Pipeline] Promoted partial results to retained_earnings_results.json")
                except Exception as e:
                    logger.warning(f"[Pipeline] Could not promote partial results: {e}")
                logger.info("[Pipeline] Recalculating after stop...")
                subprocess.run([sys.executable, str(calc)], cwd=str(_ctx().project_root), check=True, text=True)
                logger.info("[Pipeline] Regenerating screenshots after stop...")
                subprocess.run([sys.executable, str(shots)], cwd=str(_ctx().project_root), check=True, text=True)
                # mark completed
                try:
                    progress_path = _ctx().project_root / RUNTIME_PDFS_PROGRESS_JSON
                    with open(progress_path, 'w', encoding='utf-8') as f:
                        json.dump({"status": "completed"}, f)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"[Pipeline] Finalize after stop failed: {e}")
        threading.Thread(target=_finalize_after_stop, daemon=True).start()
        return jsonify({"status": "accepted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route('/api/net_profit/stop', methods=['POST'])
def stop_net_profit():
    flag = _ctx().project_root / RUNTIME_STOP_NET_FLAG
    try:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text('stop', encoding='utf-8')
        return jsonify({"status": "accepted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/correct_retained_earnings', methods=['POST'])
def correct_retained_earnings():
    data = request.json
    company_symbol = data.get('company_symbol')
    correct_value = data.get('correct_value')
    feedback = data.get('feedback', '')
    if not company_symbol or not correct_value:
        return jsonify({'error': 'Missing company_symbol or correct_value'}), 400

    # Load retained earnings results
    results_file = _ctx().project_root / "data/results/retained_earnings_results.json"
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Failed to load results: {e}'}), 500

    # Update the value for the company
    updated = False
    for entry in results:
        if entry.get('company_symbol') == company_symbol:
            # Keep raw user-entered value (text)
            entry['value'] = correct_value
            # Apply multiplier based on detected unit (default 1)
            try:
                base_numeric = float(str(correct_value).replace(',', ''))
            except Exception:
                base_numeric = 0.0
            multiplier = entry.get('applied_multiplier', 1) or 1
            entry['numeric_value'] = base_numeric * multiplier
            entry['method'] = 'manual_correction'
            entry['confidence'] = 'high'
            entry['flag_for_review'] = False
            updated = True
            break
    if not updated:
        # If not found, add a new entry
        try:
            base_numeric = float(str(correct_value).replace(',', ''))
        except Exception:
            base_numeric = 0.0
        results.append({
            'company_symbol': company_symbol,
            'value': correct_value,
            'numeric_value': base_numeric,  # no unit info for new, leave as-is
            'method': 'manual_correction',
            'confidence': 'high',
            'flag_for_review': False,
            'success': True
        })
    # Save back
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Log the correction
    corrections_log = _ctx().project_root / "data/results/corrections_log.json"
    try:
        if corrections_log.exists():
            with open(corrections_log, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = []
        log.append({
            'company_symbol': company_symbol,
            'correct_value': correct_value,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        })
        with open(corrections_log, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass  # Don't block on logging

    # Trigger recalculation
    try:
        subprocess.run([sys.executable, str(_ctx().project_root / SCRIPT_CALCULATE_REINVESTED)], check=True)
    except Exception as e:
        return jsonify({'error': f'Correction saved, but recalculation failed: {e}'}), 500

    # Load updated CSV and return the new values for this company
    csv_file = _ctx().project_root / "data/results/reinvested_earnings_results.csv"
    try:
        df = pd.read_csv(csv_file)
        row = df[df['company_symbol'] == int(company_symbol)]
        if not row.empty:
            result = row.iloc[0].to_dict()
            return jsonify({'status': 'success', 'updated': result})
        else:
            return jsonify({'status': 'success', 'updated': None})
    except Exception as e:
        return jsonify({'status': 'success', 'updated': None, 'warning': f'Correction saved, but failed to load updated CSV: {e}'})

@bp.route('/api/correct_field_value', methods=['POST'])
def correct_field_value():
    """
    Correct any field value in the system (general purpose correction endpoint)
    """
    data = request.json
    company_symbol = data.get('company_symbol')
    field_type = data.get('field_type')
    new_value = data.get('new_value')
    feedback = data.get('feedback', '')
    quarter = data.get('quarter', 'Q1')  # Default to Q1 if not provided
    
    logger.info(
        "Received field correction field_type=%s quarter=%s symbol_len=%s",
        field_type,
        quarter,
        _symbol_len_label(company_symbol),
    )

    if not company_symbol or not field_type or new_value is None:
        logger.error(
            "Missing required fields field_type=%s has_symbol=%s has_new_value=%s quarter=%s",
            field_type,
            bool(company_symbol),
            new_value is not None,
            quarter,
        )
        return jsonify({'error': 'Missing company_symbol, field_type, or new_value'}), 400

    try:
        # Load the retained earnings flow data (CSV) which contains most of the calculated fields
        csv_path = _ctx().project_root / FLOW_CSV_RELPATH
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return jsonify({'error': 'Flow data file not found'}), 404
        
        # Read the CSV data
        df = pd.read_csv(csv_path)
        logger.info(f"CSV loaded with {len(df)} rows, columns: {list(df.columns)}")
        
        # Find the row for this company and quarter
        company_row = df[(df['company_symbol'] == int(company_symbol)) & (df['quarter'] == quarter)]
        if company_row.empty:
            logger.error(
                "Company row not found in flow data (symbol_len=%s quarter=%s)",
                _symbol_len_label(company_symbol),
                quarter,
            )
            logger.info(
                "Flow data stats rows=%s distinct_symbols=%s distinct_quarters=%s",
                len(df),
                df["company_symbol"].nunique(),
                df["quarter"].nunique(),
            )
            return jsonify({'error': f'Company {company_symbol} with quarter {quarter} not found in flow data'}), 404
        
        logger.info(f"Found company row: {company_row.iloc[0].to_dict()}")
        
        # Update the specific field based on field_type
        field_mapping = {
            'previous_quarter': 'previous_value',
            'current_quarter': 'current_value',
            'retained_earnings': 'current_value',  # Map retained_earnings to current_value
            'flow': 'flow',
            'foreign_investor_flow': 'reinvested_earnings_flow',
            'net_profit_foreign_investor': 'net_profit_foreign_investor',
            'distributed_profits_foreign_investor': 'distributed_profits_foreign_investor'
        }
        
        csv_field = field_mapping.get(field_type)
        if not csv_field:
            logger.error(f"Unknown field type: {field_type}")
            return jsonify({'error': f'Unknown field type: {field_type}'}), 400
        
        # Check if the field exists in the CSV
        if csv_field not in df.columns:
            logger.error(f"Field {csv_field} not found in CSV columns: {list(df.columns)}")
            return jsonify({'error': f'Field {csv_field} not found in CSV'}), 400
        
        # Get the old value for logging
        old_value = company_row.iloc[0][csv_field]
        logger.info(f"Updating {csv_field} from {old_value} to {new_value}")
        
        # Update the value
        df.loc[company_row.index, csv_field] = new_value
        
        # Save the updated CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info("CSV updated and saved successfully")
        
        # Log the correction
        corrections_log = _ctx().project_root / "data/results/corrections_log.json"
        try:
            if corrections_log.exists():
                with open(corrections_log, 'r', encoding='utf-8') as f:
                    log = json.load(f)
            else:
                log = []
            log.append({
                'company_symbol': company_symbol,
                'quarter': quarter,
                'field_type': field_type,
                'csv_field': csv_field,
                'old_value': old_value,
                'new_value': new_value,
                'feedback': feedback,
                'timestamp': datetime.now().isoformat()
            })
            with open(corrections_log, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            logger.info("Correction logged successfully")
        except Exception as e:
            logger.warning(f"Failed to log correction: {e}")
        
        # Return the updated row data
        updated_row = df[(df['company_symbol'] == int(company_symbol)) & (df['quarter'] == quarter)].iloc[0].to_dict()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully corrected {field_type} for company {company_symbol} quarter {quarter}',
            'updated': updated_row
        })
        
    except Exception as e:
        logger.error(f"Error correcting field value: {e}")
        return jsonify({'error': f'Failed to correct field value: {str(e)}'}), 500

@bp.route('/api/export_excel', methods=['GET'])
def export_excel():
    """
    Export dashboard table data to Excel file for a specific quarter or custom date
    """
    try:
        import sys
        from pathlib import Path
        import json
        from datetime import datetime
        
        # Get parameters from query string
        quarter_filter = request.args.get('quarter', 'Q1')
        custom_date = request.args.get('custom_date', None)
        custom_filename = request.args.get('custom_filename', None)
        
        # Add project root to Python path
        project_root = _ctx().project_root
        sys.path.insert(0, str(project_root))
        
        from src.utils.export_to_excel import ExcelExporter
        import pandas as pd
        
        # Create exporter
        exporter = ExcelExporter()
        
        # Load foreign ownership data (JSON)
        ownership_json_path = project_root / "data/ownership/foreign_ownership_data.json"
        if not ownership_json_path.exists():
            return jsonify({"error": "Ownership data file not found"}), 404
        
        with open(ownership_json_path, 'r', encoding='utf-8') as f:
            ownership_data = json.load(f)
        
        # Instead of loading static CSV, regenerate data with corrections applied
        # This ensures Excel export shows same data as dashboard
        logger.info("Regenerating flow data with corrections for Excel export...")
        try:
            # Trigger recalculation to get latest corrected data
            recalc_result = subprocess.run([sys.executable, SCRIPT_CALCULATE_REINVESTED], 
                                         capture_output=True, text=True, cwd=str(project_root))
            if recalc_result.returncode != 0:
                logger.warning(f"Recalculation had issues: {recalc_result.stderr}")
            
            # Now load the updated CSV
            csv_path = project_root / FLOW_CSV_RELPATH
            if not csv_path.exists():
                return jsonify({"error": "Retained earnings flow data file not found"}), 404
            
            flow_data = pd.read_csv(csv_path)
            logger.info(f"Loaded updated flow data with {len(flow_data)} rows for export")
        except Exception as e:
            logger.error(f"Error regenerating data for export: {e}")
            return jsonify({"error": f"Failed to update data for export: {str(e)}"}), 500
        
        # Create a map of flow data by symbol and quarter
        flow_map = {}
        for _, row in flow_data.iterrows():
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
                    'reinvested_earnings_flow': row.get('reinvested_earnings_flow', ''),
                    'net_profit_foreign_investor': row.get('net_profit_foreign_investor', ''),
                    'distributed_profits_foreign_investor': row.get('distributed_profits_foreign_investor', '')
                }
        
        # Load net profit data
        net_profit_path = project_root / QUARTERLY_NET_PROFIT_RELPATH
        net_profit_data = {}
        if net_profit_path.exists():
            with open(net_profit_path, 'r', encoding='utf-8') as f:
                net_profit_raw = json.load(f)
                for company in net_profit_raw:
                    symbol = company.get('company_symbol')
                    if symbol:
                        net_profit_data[symbol] = company
        
        # Handle custom date export
        if custom_date:
            try:
                # Parse custom date
                custom_date_obj = datetime.strptime(custom_date, '%Y-%m-%d')
                custom_year = custom_date_obj.year
                custom_month = custom_date_obj.month
                
                # Determine quarter from custom date
                if custom_month in [1, 2, 3]:
                    custom_quarter = "Q1"
                elif custom_month in [4, 5, 6]:
                    custom_quarter = "Q2"
                elif custom_month in [7, 8, 9]:
                    custom_quarter = "Q3"
                else:  # 10, 11, 12
                    custom_quarter = "Q4"

                # Override quarter filter with custom date quarter
                quarter_filter = custom_quarter
                logger.info(
                    "Custom date export maps to quarter=%s year=%s",
                    custom_quarter,
                    custom_year,
                )
                
            except ValueError:
                return jsonify({"error": "Invalid custom date format. Use YYYY-MM-DD"}), 400
        
        # Merge the data for the selected quarter only
        merged_data = []
        for ownership_row in ownership_data:
            symbol = str(ownership_row.get('symbol', '')).strip()
            flow_info = flow_map.get(symbol, {})
            net_profit_info = net_profit_data.get(symbol, {})
            
            # Only create row for the selected quarter
            quarter_data = flow_info.get(quarter_filter, {})
            
            # Get net profit for this quarter
            net_profit_value = EMPTY_DISPLAY_AR
            if net_profit_info and 'quarterly_net_profit' in net_profit_info:
                quarter_key = f"{quarter_filter} 2025"
                if quarter_key in net_profit_info['quarterly_net_profit']:
                    net_profit_value = net_profit_info['quarterly_net_profit'][quarter_key]
            
            # Get previous quarter for header
            previous_quarter = ""
            if quarter_filter == "Q1":
                previous_quarter = "2024Q4"  # This refers to Annual 2024 statement
            elif quarter_filter == "Q2":
                previous_quarter = "2025Q1"
            elif quarter_filter == "Q3":
                previous_quarter = "2025Q2"
            elif quarter_filter == "Q4":
                previous_quarter = "2025Q3"
            
            # Get current quarter for header
            current_quarter = ""
            if quarter_filter == "Q1":
                current_quarter = "2025Q1"
            elif quarter_filter == "Q2":
                current_quarter = "2025Q2"
            elif quarter_filter == "Q3":
                current_quarter = "2025Q3"
            elif quarter_filter == "Q4":
                current_quarter = "2025Q4"
            
            merged_row = {
                'رمز الشركة': symbol,
                'الشركة': ownership_row.get('company_name', ''),
                'ملكية جميع المستثمرين الأجانب': ownership_row.get('foreign_ownership', ''),
                'الملكية الحالية': ownership_row.get('max_allowed', ''),
                'ملكية المستثمر الاستراتيجي الأجنبي': ownership_row.get('investor_limit', ''),
                f'الأرباح المبقاة للربع السابق ({previous_quarter})': format_excel_cell_display(quarter_data.get('previous_value', '')),
                f'الأرباح المبقاة للربع الحالي ({current_quarter})': format_excel_cell_display(quarter_data.get('current_value', '')),
                'حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)': format_excel_cell_display(quarter_data.get('flow', '')),
                'تدفق الأرباح المبقاة للمستثمر الأجنبي': format_excel_cell_display(quarter_data.get('reinvested_earnings_flow', '')),
                'صافي الربح': net_profit_value,
                'صافي الربح للمستثمر الأجنبي': format_excel_cell_display(quarter_data.get('net_profit_foreign_investor', '')),
                'الأرباح الموزعة للمستثمر الأجنبي': format_excel_cell_display(quarter_data.get('distributed_profits_foreign_investor', ''))
            }
            merged_data.append(merged_row)
        
        # Convert to DataFrame
        data = pd.DataFrame(merged_data)
        
        # Export dashboard table
        output_path = exporter.export_dashboard_table(data)
        
        if output_path:
            # Generate filename based on whether it's custom date or quarter
            if custom_date:
                if custom_filename:
                    filename = f"{custom_filename}_{custom_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                else:
                    filename = f"financial_analysis_custom_{custom_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            else:
                if custom_filename:
                    filename = f"{custom_filename}_{quarter_filter}_2025_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                else:
                    filename = f"financial_analysis_{quarter_filter}_2025_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Return the file for download
            return send_file(
                output_path,
                as_attachment=True,
                download_name=filename,
                mimetype=MIME_XLSX
            )
        else:
            return jsonify({"error": "Failed to create Excel file"}), 500
            
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

@bp.route('/api/update_ownership', methods=['POST'])
def update_ownership_data():
    """
    Manual endpoint to update ownership data (alternative to scraper)
    """
    try:
        logger.info("Manual ownership data update requested...")
        
        # Check if ownership scraper exists and try to run it
        ownership_script = _ctx().project_root / "src/scrapers/ownership.py"
        if ownership_script.exists():
            try:
                logger.info("Attempting to run ownership scraper...")
                subprocess.run(
                    ['python', str(ownership_script)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                logger.info(MSG_OWNERSHIP_UPDATED_OK)
                return jsonify({
                    "status": "success", 
                    "message": MSG_OWNERSHIP_UPDATED_OK
                }), 200
            except subprocess.TimeoutExpired:
                logger.error("Ownership scraper timed out")
                return jsonify({
                    "status": "error", 
                    "message": "Ownership scraper timed out. Please try again later."
                }), 500
            except subprocess.CalledProcessError as e:
                logger.error(f"Ownership scraper failed: {e.stderr}")
                return jsonify({
                    "status": "error", 
                    "message": f"Ownership scraper failed: {e.stderr}"
                }), 500
        else:
            return jsonify({
                "status": "error", 
                "message": "Ownership scraper not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating ownership data: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to update ownership data: {str(e)}"
        }), 500

@bp.route('/api/ownership_snapshots', methods=['GET'])
def list_ownership_snapshots():
    """
    List all archived quarterly Excel files for user download
    """
    from pathlib import Path
    import re
    project_root = _ctx().project_root
    archives_dir = project_root / 'output' / 'archives'
    result = []
    if not archives_dir.exists():
        return jsonify([])
    for quarter_dir in sorted(archives_dir.iterdir()):
        if quarter_dir.is_dir():
            # Example: output/archives/2024_Q2/financial_analysis_2024_Q2.xlsx
            for file in quarter_dir.glob('financial_analysis_*.xlsx'):
                # Extract year and quarter from folder name
                m = re.match(r'(\d{4})_Q(\d+)', quarter_dir.name)
                if m:
                    year = int(m.group(1))
                    quarter = int(m.group(2))
                else:
                    year = None
                    quarter = None
                # Use file modified time as snapshot date
                snapshot_date = file.stat().st_mtime
                from datetime import datetime
                snapshot_date_str = datetime.fromtimestamp(snapshot_date).strftime('%Y-%m-%d')
                result.append({
                    'quarter': f'Q{quarter}',
                    'year': year,
                    'snapshot_date': snapshot_date_str,
                    'download_url': f'/snapshots/{year}_Q{quarter}.xlsx'
                })
    return jsonify(result)



@bp.route('/snapshots/<year_q>.xlsx', methods=['GET'])
def download_snapshot(year_q):
    """
    Download a specific archived Excel file by year and quarter
    """
    from pathlib import Path
    project_root = _ctx().project_root
    archives_dir = project_root / 'output' / 'archives'
    # year_q is like 2024_Q2
    file_path = archives_dir / year_q / f'financial_analysis_{year_q}.xlsx'
    if not file_path.exists():
        return jsonify({'error': MSG_FILE_NOT_FOUND}), 404
    return send_file(str(file_path), as_attachment=True, download_name=f'ownership_{year_q}.xlsx', mimetype=MIME_XLSX)

@bp.route('/api/user_exports', methods=['GET'])
def list_user_exports():
    """
    List all user-triggered Excel exports in output/excel/
    """
    from pathlib import Path
    from datetime import datetime
    project_root = _ctx().project_root
    user_exports_dir = project_root / 'output' / 'excel'
    result = []
    if not user_exports_dir.exists():
        return jsonify([])
    for file in sorted(user_exports_dir.glob('financial_analysis_*.xlsx'), key=lambda f: f.stat().st_mtime, reverse=True):
        export_date = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        result.append({
            'filename': file.name,
            'export_date': export_date,
            'download_url': f'/user_exports/{file.name}'
        })
    return jsonify(result)

@bp.route('/user_exports/<filename>', methods=['GET'])
def download_user_export(filename):
    """
    Download a user-triggered Excel export by filename
    """
    from pathlib import Path
    project_root = _ctx().project_root
    user_exports_dir = project_root / 'output' / 'excel'
    file_path = user_exports_dir / filename
    if not file_path.exists():
        return jsonify({'error': MSG_FILE_NOT_FOUND}), 404
    return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype=MIME_XLSX)

@bp.route('/api/user_exports/<filename>', methods=['DELETE'])
def delete_user_export(filename):
    """
    Delete a user-triggered Excel export by filename
    """
    from pathlib import Path
    project_root = _ctx().project_root
    user_exports_dir = project_root / 'output' / 'excel'
    file_path = user_exports_dir / filename
    if not file_path.exists():
        return jsonify({'error': MSG_FILE_NOT_FOUND}), 404
    try:
        file_path.unlink()
        return jsonify({'status': 'success', 'message': 'File deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/net-profit', methods=['GET'])
def get_net_profit():
    """Get quarterly net profit data for all companies."""
    try:
        net_profit_file = _ctx().project_root / QUARTERLY_NET_PROFIT_RELPATH
        if not net_profit_file.exists():
            return jsonify({'error': 'Net profit data not found'}), 404
            
        with open(net_profit_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to lookup format for easier frontend use
        lookup_data = {}
        for company in data:
            symbol = company.get('company_symbol')
            if symbol:
                lookup_data[symbol] = company
        
        return jsonify(lookup_data)
        
    except Exception as e:
        print(f"Error serving net profit data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/evidence/<company_symbol>/quarter_mapping', methods=['GET'])
def get_quarter_evidence_mapping(company_symbol):
    """
    Get evidence mapping for a specific company showing which screenshots correspond to which quarter references
    """
    try:
        # Get quarter parameter from query string
        quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025
        
        # Define the mapping logic for quarter references
        mapping_info = {
            'requested_quarter': quarter,
            'company_symbol': company_symbol,
            'evidence_mapping': {}
        }
        
        if quarter == "Q1_2025":
            # Q1 2025: current quarter = Q1 2025, previous quarter = Annual 2024
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': 'Q1 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q1_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع الحالي (2025Q1)'
                },
                'previous_quarter': {
                    'reference': 'Annual 2024',
                    'screenshot_pattern': f"{company_symbol}_*_annual_2024_evidence.png",
                    'description': 'الأرباح المبقاة للربع السابق (2024Q4) - Annual Statement'
                }
            }
        elif quarter == "Q2_2025":
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': 'Q2 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q2_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع الحالي (2025Q2)'
                },
                'previous_quarter': {
                    'reference': 'Q1 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q1_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع السابق (2025Q1)'
                }
            }
        elif quarter == "Q3_2025":
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': 'Q3 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q3_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع الحالي (2025Q3)'
                },
                'previous_quarter': {
                    'reference': 'Q2 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q2_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع السابق (2025Q2)'
                }
            }
        elif quarter == "Q4_2025":
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': 'Q4 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q4_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع الحالي (2025Q4)'
                },
                'previous_quarter': {
                    'reference': 'Q3 2025',
                    'screenshot_pattern': f"{company_symbol}_*_q3_2025_evidence.png",
                    'description': 'الأرباح المبقاة للربع السابق (2025Q3)'
                }
            }
        elif quarter == "Annual_2024":
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': 'Annual 2024',
                    'screenshot_pattern': f"{company_symbol}_*_annual_2024_evidence.png",
                    'description': 'الأرباح المبقاة للربع السابق (2024Q4) - Annual Statement'
                },
                'note': 'This is the annual statement that serves as the previous quarter reference for Q1 2025'
            }
        else:
            # Default fallback
            mapping_info['evidence_mapping'] = {
                'current_quarter': {
                    'reference': quarter,
                    'screenshot_pattern': f"{company_symbol}_*_evidence.png",
                    'description': f'Evidence for {quarter}'
                }
            }
        
        # Check which screenshots actually exist
        for quarter_type, info in mapping_info['evidence_mapping'].items():
            pattern = info['screenshot_pattern']
            screenshot_files = list(_ctx().screenshots_dir.glob(pattern))
            info['screenshots_found'] = [f.name for f in screenshot_files]
            info['has_evidence'] = len(screenshot_files) > 0
            if screenshot_files:
                info['primary_screenshot'] = screenshot_files[0].name
                info['screenshot_url'] = f"/api/evidence/{company_symbol}.png?quarter={quarter}"
        
        return jsonify(mapping_info)
        
    except Exception as e:
        logger.error(
            "Error getting quarter mapping (symbol_len=%s): %s",
            _symbol_len_label(company_symbol),
            type(e).__name__,
        )
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/evidence/<company_symbol>/previous_quarter', methods=['GET'])
def get_previous_quarter_evidence(company_symbol):
    """
    Get evidence for the previous quarter reference (especially useful for Q1 where previous = Annual)
    """
    try:
        # Get quarter parameter from query string
        quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025
        
        # Determine what the "previous quarter" should be
        previous_quarter_pattern = ""
        if quarter in ("Q1_2025", "Annual_2024"):
            # Q1: previous is Annual 2024; Annual_2024 uses the same evidence pattern
            previous_quarter_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
            previous_quarter_description = "Annual 2024 (الأرباح المبقاة للربع السابق)"
        elif quarter == "Q2_2025":
            previous_quarter_pattern = f"{company_symbol}_*_q1_2025_evidence.png"
            previous_quarter_description = "Q1 2025"
        elif quarter == "Q3_2025":
            previous_quarter_pattern = f"{company_symbol}_*_q2_2025_evidence.png"
            previous_quarter_description = "Q2 2025"
        elif quarter == "Q4_2025":
            previous_quarter_pattern = f"{company_symbol}_*_q3_2025_evidence.png"
            previous_quarter_description = "Q3 2025"
        else:
            # Fallback
            previous_quarter_pattern = f"{company_symbol}_*_evidence.png"
            previous_quarter_description = "Any available evidence"
        
        # Search for previous quarter screenshot
        screenshot_files = list(_ctx().screenshots_dir.glob(previous_quarter_pattern))
        
        if not screenshot_files:
            return jsonify({
                "error": "Previous quarter evidence not found",
                "company_symbol": company_symbol,
                "requested_quarter": quarter,
                "previous_quarter_pattern": previous_quarter_pattern,
                "description": previous_quarter_description
            }), 404
        
        # Return the previous quarter evidence info
        screenshot_path = screenshot_files[0]
        return jsonify({
            "company_symbol": company_symbol,
            "requested_quarter": quarter,
            "previous_quarter_description": previous_quarter_description,
            "previous_quarter_pattern": previous_quarter_pattern,
            "screenshots_found": [f.name for f in screenshot_files],
            "primary_screenshot": screenshot_path.name,
            "screenshot_url": f"/api/evidence/{company_symbol}.png?quarter={quarter}",
            "note": "This endpoint specifically handles the case where 'previous quarter' for Q1 refers to Annual statement"
        })
        
    except Exception as e:
        logger.error(
            "Error getting previous quarter evidence (symbol_len=%s): %s",
            _symbol_len_label(company_symbol),
            type(e).__name__,
        )
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500

@bp.route('/api/trigger_quarterly_archive', methods=['POST'])
def trigger_quarterly_archive():
    """
    Manually trigger the quarterly archiving process for testing
    """
    try:
        logger.info("Manual quarterly archive trigger requested...")
        
        # Call the scheduled function directly
        run_quarterly_refresh_and_archive(_ctx().project_root)
        
        return jsonify({
            "status": "success", 
            "message": "Quarterly archiving process completed successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in manual quarterly archive trigger: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Quarterly archiving failed: {str(e)}"
        }), 500

