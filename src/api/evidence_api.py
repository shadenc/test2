#!/usr/bin/env python3
"""
Flask API for serving evidence screenshots and extraction metadata
"""

from flask import Flask, send_file, jsonify, request, make_response
from flask_cors import CORS
import json
import os
from pathlib import Path
import logging
import subprocess
from datetime import datetime
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    # Allow CORS from React frontend
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Always resolve paths relative to the project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    SCREENSHOTS_DIR = PROJECT_ROOT / "output/screenshots"
    RESULTS_FILE = PROJECT_ROOT / "data/results/retained_earnings_results.json"
    METADATA_FILE = SCREENSHOTS_DIR / "evidence_metadata.json"
    CSV_FILE = PROJECT_ROOT / "data/results/reinvested_earnings_results.csv"
    FLOW_CSV_FILE = PROJECT_ROOT / "data/results/retained_earnings_flow.csv"  # New flow data file

    @app.route('/api/evidence/<company_symbol>.png')
    def get_evidence_screenshot(company_symbol):
        """
        Serve evidence screenshot for a specific company and quarter
        """
        try:
            # Get quarter parameter from query string
            quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025
            
            # Map quarter parameter to screenshot search pattern
            # Handle the special case where "previous quarter" for Q1 refers to annual statement
            quarter_pattern = ""
            if quarter == "Q4_2024":
                quarter_pattern = f"{company_symbol}_*_q4_2024_evidence.png"
            elif quarter == "Q1_2025":
                # Q1 2025 previous quarter is Annual 2024, so look for both
                quarter_pattern = f"{company_symbol}_*_q1_2025_evidence.png"
                # Also look for annual 2024 as fallback since it's the "previous quarter" reference
                fallback_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
            elif quarter == "Q2_2025":
                quarter_pattern = f"{company_symbol}_*_q2_2025_evidence.png"
            elif quarter == "Q3_2025":
                quarter_pattern = f"{company_symbol}_*_q3_2025_evidence.png"
            elif quarter == "Q4_2025":
                quarter_pattern = f"{company_symbol}_*_q4_2025_evidence.png"
            elif quarter == "Annual_2024":
                # Direct request for Annual 2024 evidence
                quarter_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
            else:
                # Fallback: search for any evidence for this company
                quarter_pattern = f"{company_symbol}_*_evidence.png"
            
            # Search for screenshot files for the specific quarter
            screenshot_files = list(SCREENSHOTS_DIR.glob(quarter_pattern))
            
            # Special handling for Q1_2025: if no Q1 screenshot found, try annual 2024
            if quarter == "Q1_2025" and not screenshot_files:
                logger.info(f"No Q1 2025 screenshot found for {company_symbol}, trying annual 2024 as previous quarter reference")
                screenshot_files = list(SCREENSHOTS_DIR.glob(fallback_pattern))
            
            # If no specific quarter evidence found, try to find any evidence for this company
            if not screenshot_files:
                fallback_pattern = f"{company_symbol}_*_evidence.png"
                screenshot_files = list(SCREENSHOTS_DIR.glob(fallback_pattern))
            
            if not screenshot_files:
                return jsonify({"error": "Evidence screenshot not found"}), 404
            
            # Use the first available screenshot
            screenshot_path = screenshot_files[0]
            logger.info(f"Serving screenshot: {screenshot_path} for company {company_symbol} quarter {quarter}")
            
            return send_file(str(screenshot_path), mimetype='image/png')
            
        except Exception as e:
            logger.error(f"Error serving screenshot for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/extractions')
    def get_extractions():
        """
        Get all extraction results with evidence information
        """
        try:
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Load evidence metadata if available
            evidence_metadata = {}
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
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
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/extractions/<company_symbol>')
    def get_extraction_by_company(company_symbol):
        """
        Get extraction result for a specific company and quarter
        """
        try:
            # Get quarter parameter from query string
            quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025
            
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Find the specific company
            company_result = None
            for result in results:
                if result['company_symbol'] == company_symbol:
                    company_result = result
                    break
            
            if not company_result:
                return jsonify({"error": "Company not found"}), 404
            
            # Map quarter parameter to screenshot search pattern
            quarter_pattern = ""
            if quarter == "Q4_2024":
                quarter_pattern = f"{company_symbol}_*_q4_2024_evidence.png"
            elif quarter == "Q1_2025":
                # Q1 2025 previous quarter is Annual 2024, so look for both
                quarter_pattern = f"{company_symbol}_*_q1_2025_evidence.png"
                # Also look for annual 2024 as fallback since it's the "previous quarter" reference
                fallback_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
            elif quarter == "Q2_2025":
                quarter_pattern = f"{company_symbol}_*_q2_2025_evidence.png"
            elif quarter == "Q3_2025":
                quarter_pattern = f"{company_symbol}_*_q3_2025_evidence.png"
            elif quarter == "Q4_2025":
                quarter_pattern = f"{company_symbol}_*_q4_2025_evidence.png"
            elif quarter == "Annual_2024":
                # Direct request for Annual 2024 evidence
                quarter_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
            else:
                # Fallback: search for any evidence for this company
                quarter_pattern = f"{company_symbol}_*_evidence.png"
            
            # Check if evidence screenshot exists for the specific quarter
            screenshot_files = list(SCREENSHOTS_DIR.glob(quarter_pattern))
            has_evidence = len(screenshot_files) > 0
            
            # Special handling for Q1_2025: if no Q1 screenshot found, try annual 2024
            if quarter == "Q1_2025" and not has_evidence:
                logger.info(f"No Q1 2025 screenshot found for {company_symbol}, trying annual 2024 as previous quarter reference")
                screenshot_files = list(SCREENSHOTS_DIR.glob(fallback_pattern))
                has_evidence = len(screenshot_files) > 0
            
            # If no specific quarter evidence found, try to find any evidence for this company
            if not has_evidence:
                fallback_pattern = f"{company_symbol}_*_evidence.png"
                screenshot_files = list(SCREENSHOTS_DIR.glob(fallback_pattern))
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
            logger.error(f"Error serving extraction for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/evidence/metadata')
    def get_evidence_metadata():
        """
        Get metadata about all available evidence screenshots
        """
        try:
            if not METADATA_FILE.exists():
                return jsonify({"evidence_screenshots": []})
            
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return jsonify({
                "evidence_screenshots": metadata,
                "total_screenshots": len(metadata)
            })
            
        except Exception as e:
            logger.error(f"Error serving evidence metadata: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/evidence/<company_symbol>')
    def get_evidence(company_symbol):
        """
        Get evidence data for a specific company
        """
        try:
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
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
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
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
                screenshot_filename = f"{company_symbol}_evidence.png"
                response['screenshot_url'] = f"/api/evidence/{company_symbol}.png"
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error serving evidence for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/retained_earnings_flow.csv')
    def get_retained_earnings_flow_csv():
        """Get retained earnings flow data as CSV."""
        try:
            csv_path = PROJECT_ROOT / "data/results/retained_earnings_flow.csv"
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

    @app.route('/api/reinvested_earnings_results.csv')
    def get_reinvested_earnings_results():
        """
        Serve reinvested earnings results as CSV (legacy endpoint)
        """
        try:
            if not CSV_FILE.exists():
                logger.warning(f"CSV file not found: {CSV_FILE}")
                return jsonify({"error": "Data not available"}), 404
            
            return send_file(
                str(CSV_FILE), 
                mimetype='text/csv',
                as_attachment=True,
                download_name='reinvested_earnings_results.csv'
            )
            
        except Exception as e:
            logger.error(f"Error serving CSV: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/refresh', methods=['POST'])
    def refresh_data():
        """
        Refreshes the data by recalculating reinvested earnings and regenerating evidence screenshots.
        Note: Ownership data scraping is disabled due to browser issues.
        """
        try:
            logger.info("Starting data refresh...")
            
            # 1. Recalculate reinvested earnings (this is the main step)
            logger.info("Recalculating reinvested earnings...")
            try:
                subprocess.run(['python', 'src/calculators/calculate_reinvested_earnings.py'], 
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
                subprocess.run(['python', 'src/utils/generate_evidence_screenshots.py'], 
                             check=True, capture_output=True, text=True)
                logger.info("Evidence screenshots regeneration completed successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Evidence screenshots regeneration failed: {e}")
                # Don't fail the entire refresh for this step
                pass
            
            logger.info("Data refresh completed successfully")
            return jsonify({
                "status": "success", 
                "message": "Data refreshed successfully. Note: Ownership data was not updated due to browser issues."
            }), 200
            
        except Exception as e:
            logger.error(f"Error during data refresh: {e}")
            return jsonify({
                "status": "error", 
                "message": f"Refresh failed: {str(e)}"
            }), 500

    @app.route('/api/health')
    def health_check():
        """
        Health check endpoint
        """
        return jsonify({
            "status": "healthy",
            "screenshots_dir": str(SCREENSHOTS_DIR),
            "screenshots_available": SCREENSHOTS_DIR.exists()
        })

    @app.route('/api/correct_retained_earnings', methods=['POST'])
    def correct_retained_earnings():
        data = request.json
        company_symbol = data.get('company_symbol')
        correct_value = data.get('correct_value')
        feedback = data.get('feedback', '')
        if not company_symbol or not correct_value:
            return jsonify({'error': 'Missing company_symbol or correct_value'}), 400

        # Load retained earnings results
        results_file = PROJECT_ROOT / "data/results/retained_earnings_results.json"
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            return jsonify({'error': f'Failed to load results: {e}'}), 500

        # Update the value for the company
        updated = False
        for entry in results:
            if entry.get('company_symbol') == company_symbol:
                entry['value'] = correct_value
                entry['numeric_value'] = float(str(correct_value).replace(',', ''))
                entry['method'] = 'manual_correction'
                entry['confidence'] = 'high'
                entry['flag_for_review'] = False
                updated = True
                break
        if not updated:
            # If not found, add a new entry
            results.append({
                'company_symbol': company_symbol,
                'value': correct_value,
                'numeric_value': float(str(correct_value).replace(',', '')),
                'method': 'manual_correction',
                'confidence': 'high',
                'flag_for_review': False,
                'success': True
            })
        # Save back
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Log the correction
        corrections_log = PROJECT_ROOT / "data/results/corrections_log.json"
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
            subprocess.run(["python", str(PROJECT_ROOT / "src/calculators/calculate_reinvested_earnings.py")], check=True)
        except Exception as e:
            return jsonify({'error': f'Correction saved, but recalculation failed: {e}'}), 500

        # Load updated CSV and return the new values for this company
        csv_file = PROJECT_ROOT / "data/results/reinvested_earnings_results.csv"
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

    @app.route('/api/correct_field_value', methods=['POST'])
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
        
        logger.info(f"Received correction request: company_symbol={company_symbol}, field_type={field_type}, new_value={new_value}, quarter={quarter}")
        
        if not company_symbol or not field_type or new_value is None:
            logger.error(f"Missing required fields: company_symbol={company_symbol}, field_type={field_type}, new_value={new_value}")
            return jsonify({'error': 'Missing company_symbol, field_type, or new_value'}), 400

        try:
            # Load the retained earnings flow data (CSV) which contains most of the calculated fields
            csv_path = PROJECT_ROOT / "data/results/retained_earnings_flow.csv"
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_path}")
                return jsonify({'error': 'Flow data file not found'}), 404
            
            # Read the CSV data
            df = pd.read_csv(csv_path)
            logger.info(f"CSV loaded with {len(df)} rows, columns: {list(df.columns)}")
            
            # Find the row for this company and quarter
            company_row = df[(df['company_symbol'] == int(company_symbol)) & (df['quarter'] == quarter)]
            if company_row.empty:
                logger.error(f"Company {company_symbol} with quarter {quarter} not found in flow data")
                logger.info(f"Available companies: {df['company_symbol'].unique()}")
                logger.info(f"Available quarters: {df['quarter'].unique()}")
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
            logger.info(f"CSV updated and saved successfully")
            
            # Log the correction
            corrections_log = PROJECT_ROOT / "data/results/corrections_log.json"
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

    @app.route('/api/export_excel', methods=['GET'])
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
            project_root = Path(__file__).parent.parent.parent
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
            
            # Load retained earnings flow data (CSV) - NEW DATA SOURCE
            csv_path = project_root / "data/results/retained_earnings_flow.csv"
            if not csv_path.exists():
                return jsonify({"error": "Retained earnings flow data file not found"}), 404
            
            flow_data = pd.read_csv(csv_path)
            
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
            net_profit_path = project_root / "data/results/quarterly_net_profit.json"
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
                        previous_quarter = "Q4"
                        previous_year = custom_year - 1
                    elif custom_month in [4, 5, 6]:
                        custom_quarter = "Q2"
                        previous_quarter = "Q1"
                        previous_year = custom_year
                    elif custom_month in [7, 8, 9]:
                        custom_quarter = "Q3"
                        previous_quarter = "Q2"
                        previous_year = custom_year
                    else:  # 10, 11, 12
                        custom_quarter = "Q4"
                        previous_quarter = "Q3"
                        previous_year = custom_year
                    
                    # Override quarter filter with custom date quarter
                    quarter_filter = custom_quarter
                    logger.info(f"Custom date {custom_date} maps to quarter {custom_quarter} {custom_year}")
                    
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
                net_profit_value = "لايوجد"
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
                
                # Add evidence mapping information for debugging
                evidence_note = ""
                if quarter_filter == "Q1":
                    evidence_note = "Note: Previous quarter (2024Q4) refers to Annual 2024 statement screenshot"
                elif quarter_filter == "Q2":
                    evidence_note = "Note: Previous quarter (2025Q1) refers to Q1 2025 statement screenshot"
                elif quarter_filter == "Q3":
                    evidence_note = "Note: Previous quarter (2025Q2) refers to Q2 2025 statement screenshot"
                elif quarter_filter == "Q4":
                    evidence_note = "Note: Previous quarter (2025Q3) refers to Q3 2025 statement screenshot"
                
                merged_row = {
                    'رمز الشركة': symbol,
                    'الشركة': ownership_row.get('company_name', ''),
                    'ملكية جميع المستثمرين الأجانب': ownership_row.get('foreign_ownership', ''),
                    'الملكية الحالية': ownership_row.get('max_allowed', ''),
                    'ملكية المستثمر الاستراتيجي الأجنبي': ownership_row.get('investor_limit', ''),
                    f'الأرباح المبقاة للربع السابق ({previous_quarter})': quarter_data.get('previous_value', 'لايوجد'),
                    f'الأرباح المبقاة للربع الحالي ({current_quarter})': quarter_data.get('current_value', 'لايوجد'),
                    'حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)': quarter_data.get('flow', 'لايوجد'),
                    'تدفق الأرباح المبقاة للمستثمر الأجنبي': quarter_data.get('reinvested_earnings_flow', 'لايوجد'),
                    'صافي الربح': net_profit_value,
                    'صافي الربح للمستثمر الأجنبي': quarter_data.get('net_profit_foreign_investor', 'لايوجد'),
                    'الأرباح الموزعة للمستثمر الأجنبي': quarter_data.get('distributed_profits_foreign_investor', 'لايوجد'),
                    'ملاحظة الأدلة': evidence_note
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
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                return jsonify({"error": "Failed to create Excel file"}), 500
                
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return jsonify({"error": f"Export failed: {str(e)}"}), 500

    @app.route('/api/update_ownership', methods=['POST'])
    def update_ownership_data():
        """
        Manual endpoint to update ownership data (alternative to scraper)
        """
        try:
            logger.info("Manual ownership data update requested...")
            
            # Check if ownership scraper exists and try to run it
            ownership_script = PROJECT_ROOT / "src/scrapers/ownership.py"
            if ownership_script.exists():
                try:
                    logger.info("Attempting to run ownership scraper...")
                    result = subprocess.run(['python', str(ownership_script)], 
                                         check=True, capture_output=True, text=True, timeout=300)
                    logger.info("Ownership data updated successfully")
                    return jsonify({
                        "status": "success", 
                        "message": "Ownership data updated successfully"
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

    @app.route('/api/ownership_snapshots')
    def list_ownership_snapshots():
        """
        List all archived quarterly Excel files for user download
        """
        from pathlib import Path
        import re
        project_root = Path(__file__).parent.parent.parent
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



    @app.route('/snapshots/<year_q>.xlsx')
    def download_snapshot(year_q):
        """
        Download a specific archived Excel file by year and quarter
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        archives_dir = project_root / 'output' / 'archives'
        # year_q is like 2024_Q2
        file_path = archives_dir / year_q / f'financial_analysis_{year_q}.xlsx'
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        return send_file(str(file_path), as_attachment=True, download_name=f'ownership_{year_q}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    @app.route('/api/user_exports')
    def list_user_exports():
        """
        List all user-triggered Excel exports in output/excel/
        """
        from pathlib import Path
        from datetime import datetime
        project_root = Path(__file__).parent.parent.parent
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

    @app.route('/user_exports/<filename>')
    def download_user_export(filename):
        """
        Download a user-triggered Excel export by filename
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        user_exports_dir = project_root / 'output' / 'excel'
        file_path = user_exports_dir / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    @app.route('/api/user_exports/<filename>', methods=['DELETE'])
    def delete_user_export(filename):
        """
        Delete a user-triggered Excel export by filename
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        user_exports_dir = project_root / 'output' / 'excel'
        file_path = user_exports_dir / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        try:
            file_path.unlink()
            return jsonify({'status': 'success', 'message': 'File deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/net-profit')
    def get_net_profit():
        """Get quarterly net profit data for all companies."""
        try:
            net_profit_file = PROJECT_ROOT / "data/results/quarterly_net_profit.json"
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

    @app.route('/api/evidence/<company_symbol>/quarter_mapping')
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
                screenshot_files = list(SCREENSHOTS_DIR.glob(pattern))
                info['screenshots_found'] = [f.name for f in screenshot_files]
                info['has_evidence'] = len(screenshot_files) > 0
                if screenshot_files:
                    info['primary_screenshot'] = screenshot_files[0].name
                    info['screenshot_url'] = f"/api/evidence/{company_symbol}.png?quarter={quarter}"
            
            return jsonify(mapping_info)
            
        except Exception as e:
            logger.error(f"Error getting quarter mapping for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/evidence/<company_symbol>/previous_quarter')
    def get_previous_quarter_evidence(company_symbol):
        """
        Get evidence for the previous quarter reference (especially useful for Q1 where previous = Annual)
        """
        try:
            # Get quarter parameter from query string
            quarter = request.args.get('quarter', 'Q1_2025')  # Default to Q1 2025
            
            # Determine what the "previous quarter" should be
            previous_quarter_pattern = ""
            if quarter == "Q1_2025":
                # Q1 2025 previous quarter is Annual 2024
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
            elif quarter == "Annual_2024":
                # Direct request for Annual 2024 evidence
                previous_quarter_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
                previous_quarter_description = "Annual 2024 (الأرباح المبقاة للربع السابق)"
            else:
                # Fallback
                previous_quarter_pattern = f"{company_symbol}_*_evidence.png"
                previous_quarter_description = "Any available evidence"
            
            # Search for previous quarter screenshot
            screenshot_files = list(SCREENSHOTS_DIR.glob(previous_quarter_pattern))
            
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
            logger.error(f"Error getting previous quarter evidence for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/trigger_quarterly_archive', methods=['POST'])
    def trigger_quarterly_archive():
        """
        Manually trigger the quarterly archiving process for testing
        """
        try:
            logger.info("Manual quarterly archive trigger requested...")
            
            # Call the scheduled function directly
            scheduled_refresh_and_archive()
            
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

    # --- Quarterly Scheduler Setup ---
    def scheduled_refresh_and_archive():
        """
        Enhanced quarterly refresh and archive function that:
        1. Automatically detects current quarter
        2. Uses the correct data sources (retained_earnings_flow.csv)
        3. Creates proper quarterly archives with correct naming
        4. Handles the quarter mapping logic properly
        """
        try:
            logger.info("[Scheduler] Running quarterly refresh and archive...")
            
            # 1. Recalculate reinvested earnings
            logger.info("[Scheduler] Step 1: Recalculating reinvested earnings...")
            subprocess.run(['python', 'src/calculators/calculate_reinvested_earnings.py'], 
                         check=True, capture_output=True, text=True)
            logger.info("[Scheduler] ✅ Reinvested earnings calculation completed")
            
            # 2. Regenerate evidence screenshots
            logger.info("[Scheduler] Step 2: Regenerating evidence screenshots...")
            subprocess.run(['python', 'src/utils/generate_evidence_screenshots.py'], 
                         check=True, capture_output=True, text=True)
            logger.info("[Scheduler] ✅ Evidence screenshots regeneration completed")
            
            # 3. Export Excel for each quarter and archive
            logger.info("[Scheduler] Step 3: Exporting and archiving quarterly data...")
            
            from src.utils.export_to_excel import ExcelExporter
            import pandas as pd
            import json
            from datetime import datetime
            from pathlib import Path
            
            project_root = Path(__file__).parent.parent.parent
            
            # Create exporter
            exporter = ExcelExporter()
            
            # Load foreign ownership data (JSON)
            ownership_json_path = project_root / "data/ownership/foreign_ownership_data.json"
            if not ownership_json_path.exists():
                logger.error("[Scheduler] ❌ Ownership data file not found")
                return
                
            with open(ownership_json_path, 'r', encoding='utf-8') as f:
                ownership_data = json.load(f)
            
            # Load retained earnings flow data (CSV) - NEW DATA SOURCE
            csv_path = project_root / "data/results/retained_earnings_flow.csv"
            if not csv_path.exists():
                logger.error("[Scheduler] ❌ Retained earnings flow data file not found")
                return
                
            flow_data = pd.read_csv(csv_path)
            
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
            
            # Get current date and determine quarter
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Determine current quarter
            if current_month in [1, 2, 3]:
                current_quarter = "Q1"
                previous_quarter = "Q4"
                previous_year = current_year - 1
            elif current_month in [4, 5, 6]:
                current_quarter = "Q2"
                previous_quarter = "Q1"
                previous_year = current_year
            elif current_month in [7, 8, 9]:
                current_quarter = "Q3"
                previous_quarter = "Q2"
                previous_year = current_year
            else:  # 10, 11, 12
                current_quarter = "Q4"
                previous_quarter = "Q3"
                previous_year = current_year
            
            logger.info(f"[Scheduler] Current quarter: {current_quarter} {current_year}")
            logger.info(f"[Scheduler] Previous quarter: {previous_quarter} {previous_year}")
            
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
            
            # Export and archive for the current quarter
            logger.info(f"[Scheduler] Exporting data for {current_quarter} {current_year}...")
            
            # Merge the data for the current quarter
            merged_data = []
            for ownership_row in ownership_data:
                symbol = str(ownership_row.get('symbol', '')).strip()
                flow_info = flow_map.get(symbol, {})
                net_profit_info = net_profit_data.get(symbol, {})
                
                # Get data for current quarter
                quarter_data = flow_info.get(current_quarter, {})
                
                # Get net profit for this quarter
                net_profit_value = "لايوجد"
                if net_profit_info and 'quarterly_net_profit' in net_profit_info:
                    quarter_key = f"{current_quarter} {current_year}"
                    if quarter_key in net_profit_info['quarterly_net_profit']:
                        net_profit_value = net_profit_info['quarterly_net_profit'][quarter_key]
                
                # Get previous quarter for header
                if current_quarter == "Q1":
                    previous_quarter_header = f"{previous_year}Q4"  # This refers to Annual previous year
                else:
                    previous_quarter_header = f"{current_year}{previous_quarter}"
                
                # Get current quarter for header
                current_quarter_header = f"{current_year}{current_quarter}"
                
                # Add evidence mapping information
                evidence_note = ""
                if current_quarter == "Q1":
                    evidence_note = "Note: Previous quarter refers to Annual statement screenshot"
                elif current_quarter == "Q2":
                    evidence_note = "Note: Previous quarter refers to Q1 statement screenshot"
                elif current_quarter == "Q3":
                    evidence_note = "Note: Previous quarter refers to Q2 statement screenshot"
                elif current_quarter == "Q4":
                    evidence_note = "Note: Previous quarter refers to Q3 statement screenshot"
                
                merged_row = {
                    'رمز الشركة': symbol,
                    'الشركة': ownership_row.get('company_name', ''),
                    'ملكية جميع المستثمرين الأجانب': ownership_row.get('foreign_ownership', ''),
                    'الملكية الحالية': ownership_row.get('max_allowed', ''),
                    'ملكية المستثمر الاستراتيجي الأجنبي': ownership_row.get('investor_limit', ''),
                    f'الأرباح المبقاة للربع السابق ({previous_quarter_header})': quarter_data.get('previous_value', 'لايوجد'),
                    f'الأرباح المبقاة للربع الحالي ({current_quarter_header})': quarter_data.get('current_value', 'لايوجد'),
                    'حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)': quarter_data.get('flow', 'لايوجد'),
                    'تدفق الأرباح المبقاة للمستثمر الأجنبي': quarter_data.get('reinvested_earnings_flow', 'لايوجد'),
                    'صافي الربح': net_profit_value,
                    'صافي الربح للمستثمر الأجنبي': quarter_data.get('net_profit_foreign_investor', 'لايوجد'),
                    'الأرباح الموزعة للمستثمر الأجنبي': quarter_data.get('distributed_profits_foreign_investor', 'لايوجد'),
                    'ملاحظة الأدلة': evidence_note
                }
                merged_data.append(merged_row)
            
            # Convert to DataFrame
            data = pd.DataFrame(merged_data)
            
            # Export dashboard table
            output_path = exporter.export_dashboard_table(data)
            
            if output_path:
                # 4. Archive results
                archive_dir = project_root / f"output/archives/{current_year}_{current_quarter}"
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy the exported Excel file to archives
                archive_excel_name = f"financial_analysis_{current_year}_{current_quarter}.xlsx"
                archive_excel_path = archive_dir / archive_excel_name
                shutil.copy(output_path, archive_excel_path)
                
                # Copy the CSV data file
                archive_csv_name = f"retained_earnings_flow_{current_year}_{current_quarter}.csv"
                archive_csv_path = archive_dir / archive_csv_name
                shutil.copy(csv_path, archive_csv_path)
                
                # Copy evidence screenshots directory for this quarter
                screenshots_archive_dir = archive_dir / "evidence_screenshots"
                screenshots_archive_dir.mkdir(exist_ok=True)
                
                # Copy relevant screenshots for this quarter
                screenshots_dir = project_root / "output/screenshots"
                if screenshots_dir.exists():
                    # Copy screenshots that match this quarter
                    quarter_pattern = f"*_{current_quarter.lower()}_{current_year}_evidence.png"
                    for screenshot in screenshots_dir.glob(quarter_pattern):
                        shutil.copy(screenshot, screenshots_archive_dir / screenshot.name)
                
                logger.info(f"[Scheduler] ✅ Archived results to {archive_dir}")
                logger.info(f"[Scheduler] ✅ Excel file: {archive_excel_name}")
                logger.info(f"[Scheduler] ✅ CSV file: {archive_csv_name}")
                logger.info(f"[Scheduler] ✅ Evidence screenshots copied")
                
            else:
                logger.error("[Scheduler] ❌ Failed to export Excel file")
                
        except Exception as e:
            logger.error(f"[Scheduler] ❌ Error in scheduled refresh: {e}")
            import traceback
            logger.error(f"[Scheduler] Traceback: {traceback.format_exc()}")

    # Start scheduler only once (avoid in child processes)
    if os.environ.get('WERKZEUG_RUN_MAIN', 'true') == 'true':
        scheduler = BackgroundScheduler()
        
        # Schedule quarterly refresh and archive
        # Run at the end of each quarter: March 31, June 30, September 30, December 31
        scheduler.add_job(
            scheduled_refresh_and_archive,
            'cron',
            month='3,6,9,12',
            day='last',
            hour=23,
            minute=59,
            id='quarterly_refresh_and_archive',
            replace_existing=True
        )
        
        # Also run daily at 2 AM for testing/development (can be removed in production)
        scheduler.add_job(
            scheduled_refresh_and_archive,
            'cron',
            hour=2,
            minute=0,
            id='daily_test_archive',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("[Scheduler] ✅ Quarterly scheduler started successfully")
        logger.info("[Scheduler] 📅 Will run at end of each quarter (Mar 31, Jun 30, Sep 30, Dec 31)")
        logger.info("[Scheduler] 🧪 Daily test run at 2 AM for development")

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Ensure screenshots directory exists (use absolute path)
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    (PROJECT_ROOT / "output/screenshots").mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Evidence API server...")
    print(f"Screenshots directory: {PROJECT_ROOT / 'output/screenshots'}")
    print(f"API will be available at: http://localhost:5003")
    
    app.run(debug=True, host='0.0.0.0', port=5003) 