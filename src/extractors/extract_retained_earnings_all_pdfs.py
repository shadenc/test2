#!/usr/bin/env python3
"""
Simple Retained Earnings Extraction from Financial Statement PDFs
Focused on extracting only retained earnings values with minimal complexity
"""

import fitz  # PyMuPDF
import re
import json
from pathlib import Path
import sqlite3
from datetime import datetime
import openai
import os
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class EvidenceScreenshotGenerator:
    """Simple screenshot generator for evidence"""
    
    def generate_highlight_screenshot(self, pdf_path: str, search_value: str, company_symbol: str) -> Optional[str]:
        """Generate screenshot highlighting the found value"""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            screenshots_dir = Path("output/screenshots")
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            # Get PDF filename for unique naming
            pdf_filename = Path(pdf_path).stem  # Remove .pdf extension
            
            # Find page with the search value and highlight it
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if search_value in text:
                    # Found the page, now highlight the value
                    page = self._highlight_value_on_page(page, search_value)
                    
                    # Take screenshot with highlighting - use unique filename
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                    screenshot_path = screenshots_dir / f"{company_symbol}_{pdf_filename}_evidence.png"
                    pix.save(str(screenshot_path))
                    doc.close()
                    return str(screenshot_path)
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    def _highlight_value_on_page(self, page, search_value: str):
        """Highlight the found value on the page with a yellow highlighter effect"""
        try:
            # Search for the text on the page
            text_instances = page.search_for(search_value)
            
            if text_instances:
                # Get the first instance and highlight it
                rect = text_instances[0]  # First occurrence
                
                # Draw a yellow highlighter effect around the found text
                highlight_rect = page.add_rect_annot(rect)
                highlight_rect.set_colors(stroke=(1, 1, 0))  # Yellow stroke
                highlight_rect.set_colors(fill=(1, 1, 0))    # Yellow fill
                highlight_rect.set_opacity(0.3)  # Semi-transparent yellow
                
                logger.info(f"Highlighted value '{search_value}' on page with yellow highlighter")
            
            return page
            
        except Exception as e:
            logger.error(f"Highlighting error: {e}")
            return page

class RetainedEarningsExtractor:
    def __init__(self):
        self.target_years = []
        self.most_recent_year = None
        
    def detect_years(self, text: str) -> List[int]:
        """Detect available years in the financial statement"""
        current_year = datetime.now().year
        
        # Look for 4-digit years (2020-2030 range)
        year_pattern = r'\b(20[2-3][0-9])\b'
        years_found = re.findall(year_pattern, text)
        
        # Convert to integers and filter realistic years
        realistic_years = []
        for year in set(int(y) for y in years_found):
            if current_year - 10 <= year <= current_year + 1:
                realistic_years.append(year)
        
        # Sort by most recent first
        realistic_years.sort(reverse=True)
        self.target_years = realistic_years
        self.most_recent_year = realistic_years[0] if realistic_years else None
        
        logger.info(f"Detected years: {realistic_years}")
        return realistic_years
    
    def extract_with_spire_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Extract using Spire.PDF if available"""
        try:
            from spire.pdf import PdfDocument, PdfTableExtractor
        except ImportError:
            return None
        
        try:
            doc = PdfDocument()
            doc.LoadFromFile(pdf_path)
            extractor = PdfTableExtractor(doc)
            
            for page_index in range(doc.Pages.Count):
                tables = extractor.ExtractTable(page_index)
                if tables:
                    for table in tables:
                        # Look for retained earnings row
                        for row_index in range(table.GetRowCount()):
                            first_col = table.GetText(row_index, 0).strip().lower()
                            if first_col == 'retained earnings':
                                # Found retained earnings row, extract values
                                for year in self.target_years:
                                    for col_index in range(table.GetColumnCount()):
                                        cell_data = table.GetText(row_index, col_index).strip()
                                        if str(year) in cell_data:
                                            # Look for numeric value in this column
                                            for row_idx in range(table.GetRowCount()):
                                                value_cell = table.GetText(row_idx, col_index).strip()
                                                if value_cell and value_cell.replace(',', '').isdigit():
                                                    numeric_value = float(value_cell.replace(',', ''))
                                                    if numeric_value >= 10000:
                                                        doc.Close()
                                                        return {
                                                            'success': True,
                                                            'value': value_cell,
                                                            'numeric_value': numeric_value,
                                                            'method': 'spire_pdf',
                                                            'year': year,
                                                            'page': page_index + 1
                                                        }
            doc.Close()
            return None
        except Exception as e:
            logger.error(f"Spire.PDF error: {e}")
            return None
    
    def extract_with_camelot(self, pdf_path: str) -> Optional[Dict]:
        """Extract using Camelot if available"""
        try:
            import camelot
        except ImportError:
            return None
        
        try:
            tables = camelot.read_pdf(pdf_path, flavor="stream")
            for table in tables:
                df = table.df
                # Look for retained earnings row
                for i, row in df.iterrows():
                    if 'retained earnings' in str(row.iloc[0]).lower():
                        # Found retained earnings row, look for years
                        for year in self.target_years:
                            for col_idx, col_name in enumerate(df.columns):
                                if str(year) in str(col_name):
                                    # Look for numeric value in this column
                                    for row_idx in range(len(df)):
                                        value = df.iloc[row_idx, col_idx]
                                        if value and str(value).replace(',', '').isdigit():
                                            numeric_value = float(str(value).replace(',', ''))
                                            if numeric_value >= 10000:
                                                return {
                                                    'success': True,
                                                    'value': str(value),
                                                    'numeric_value': numeric_value,
                                                    'method': 'camelot',
                                                    'year': year,
                                                    'page': 1
                                                }
            return None
        except Exception as e:
            logger.error(f"Camelot error: {e}")
            return None
    
    def extract_with_regex(self, pdf_path: str) -> Optional[Dict]:
        """Simple regex extraction as fallback"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Detect years first
            self.detect_years(text)
            if not self.target_years:
                return None
            
            # Look for retained earnings line
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'retained earnings' in line.lower():
                    # Look for numbers in nearby lines
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j]
                        numbers = re.findall(r'([\d,]+)', next_line)
                        for number in numbers:
                            clean_value = number.replace(',', '')
                            if clean_value.isdigit():
                                numeric_value = float(clean_value)
                                # Filter out years and small numbers
                                if numeric_value >= 10000 and numeric_value not in self.target_years:
                                    return {
                                        'success': True,
                                        'value': number,
                                        'numeric_value': numeric_value,
                                        'method': 'regex',
                                        'year': self.most_recent_year,
                                        'page': 1
                                    }
            return None
        except Exception as e:
            logger.error(f"Regex error: {e}")
            return None
    
    def extract_retained_earnings(self, pdf_path: str) -> Dict:
        """Main extraction method with fallback chain"""
        logger.info(f"Processing: {pdf_path}")
        
        # Try Spire.PDF first (most reliable)
        result = self.extract_with_spire_pdf(pdf_path)
        if result:
            return result
        
        # Try Camelot
        result = self.extract_with_camelot(pdf_path)
        if result:
            return result
        
        # Try regex as last resort
        result = self.extract_with_regex(pdf_path)
        if result:
            return result
        
        return {
            'success': False,
            'error': 'No retained earnings found using any method'
        }

def get_company_symbol_from_filename(filename):
    """Extract company symbol from PDF filename"""
    return filename.split('_')[0]

def save_to_database(results):
    """Save results to SQLite database"""
    conn = sqlite3.connect('data/financial_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS retained_earnings')
    cursor.execute('''
        CREATE TABLE retained_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_symbol TEXT,
            pdf_filename TEXT,
            retained_earnings_value REAL,
            year INTEGER,
            method TEXT,
            extraction_date TIMESTAMP
        )
    ''')
    
    for result in results:
        if result.get('success'):
            cursor.execute('''
                INSERT INTO retained_earnings 
                (company_symbol, pdf_filename, retained_earnings_value, year, method, extraction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                result['company_symbol'],
                result['pdf_filename'],
                result.get('numeric_value'),
                result.get('year'),
                result.get('method'),
                datetime.now()
            ))
    
    conn.commit()
    conn.close()

def main():
    pdf_dir = Path("data/pdfs")
    pdf_files = [f for f in pdf_dir.glob("*.pdf")]
    
    if not pdf_files:
        print("No PDF files found in data/pdfs/")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    extractor = RetainedEarningsExtractor()
    evidence_generator = EvidenceScreenshotGenerator()
    results = []
    successful_extractions = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        company_symbol = get_company_symbol_from_filename(pdf_file.name)
        result = extractor.extract_retained_earnings(str(pdf_file))
        
        # Add metadata
        result['company_symbol'] = company_symbol
        result['pdf_filename'] = pdf_file.name
        
        if result['success']:
            successful_extractions += 1
            print(f"  ✓ Found: {result['value']} (Year: {result['year']})")
            print(f"  ✓ Method: {result['method']}")
            
            # Generate evidence screenshot
            try:
                print(f"  📸 Generating evidence screenshot...")
                screenshot_path = evidence_generator.generate_highlight_screenshot(
                    str(pdf_file), result['value'], company_symbol
                )
                if screenshot_path:
                    print(f"  ✓ Evidence screenshot saved: {screenshot_path}")
                else:
                    print(f"  ⚠️ Failed to generate evidence screenshot")
            except Exception as e:
                print(f"  ⚠️ Error generating evidence screenshot: {e}")
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
        
        results.append(result)
    
    # Save results
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / "retained_earnings_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save to database
    save_to_database(results)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Successful extractions: {successful_extractions}")
    print(f"Success rate: {successful_extractions/len(pdf_files)*100:.1f}%")
    print(f"Results saved to: {output_file}")
    print(f"Results also saved to database: data/financial_analysis.db")

if __name__ == "__main__":
    main() 