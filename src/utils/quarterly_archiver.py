#!/usr/bin/env python3
"""
Quarterly Archiver Utility
Automatically organizes dashboard exports by quarter and creates quarterly archives.
"""

import logging
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class QuarterlyArchiver:
    """Handles automatic quarterly archiving of dashboard exports."""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.excel_dir = self.base_dir / "output" / "excel"
        self.archives_dir = self.base_dir / "output" / "archives"
        
        # Ensure directories exist
        self.excel_dir.mkdir(parents=True, exist_ok=True)
        self.archives_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_quarter(self) -> str:
        """Get the current quarter (Q1, Q2, Q3, Q4)."""
        today = date.today()
        month = today.month
        
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"
    
    def get_quarter_from_date(self, date_obj: date) -> str:
        """Get quarter from a specific date."""
        month = date_obj.month
        
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"
    
    def archive_existing_exports(self) -> Dict[str, List[str]]:
        """Archive existing dashboard exports by quarter."""
        logger.info("📁 Archiving existing dashboard exports...")
        
        if not self.excel_dir.exists():
            logger.warning("Excel directory doesn't exist")
            return {}
        
        # Find all financial analysis Excel files
        excel_files = list(self.excel_dir.glob("financial_analysis_*.xlsx"))
        
        if not excel_files:
            logger.info("No financial analysis files found to archive")
            return {}
        
        logger.info(f"Found {len(excel_files)} files to archive")
        
        archived_files = {}
        
        for excel_file in excel_files:
            try:
                # Extract date from filename (e.g., financial_analysis_20250817_004155.xlsx)
                filename = excel_file.stem
                date_part = filename.replace("financial_analysis_", "")
                
                # Parse the date (format: YYYYMMDD_HHMMSS)
                if len(date_part) >= 8:
                    date_str = date_part[:8]
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    
                    # Determine quarter and year
                    quarter = self.get_quarter_from_date(file_date)
                    year = file_date.year
                    
                    # Create quarter archive directory
                    quarter_dir = self.archives_dir / f"{year}_{quarter}"
                    quarter_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create archive filename
                    archive_filename = f"financial_analysis_{year}_{quarter}.xlsx"
                    archive_path = quarter_dir / archive_filename
                    
                    # Copy file to archive (don't overwrite if exists)
                    if not archive_path.exists():
                        shutil.copy2(excel_file, archive_path)
                        logger.info(f"📁 Archived {excel_file.name} to {quarter}_{year}")
                        
                        # Track archived files
                        quarter_key = f"{quarter}_{year}"
                        if quarter_key not in archived_files:
                            archived_files[quarter_key] = []
                        archived_files[quarter_key].append(str(archive_path))
                    else:
                        logger.info(f"📁 Archive already exists for {quarter}_{year}")
                        
                        # Still track existing archives
                        quarter_key = f"{quarter}_{year}"
                        if quarter_key not in archived_files:
                            archived_files[quarter_key] = []
                        archived_files[quarter_key].append(str(archive_path))
                
            except Exception as e:
                logger.error(f"Error archiving {excel_file.name}: {e}")
                continue
        
        logger.info(f"✅ Archived {len(archived_files)} quarters")
        return archived_files
    
    def create_quarterly_archive(self, quarter: str, year: int, source_file: str) -> Optional[str]:
        """Create a quarterly archive for a specific quarter."""
        try:
            # Create quarter archive directory
            quarter_dir = self.archives_dir / f"{year}_{quarter}"
            quarter_dir.mkdir(parents=True, exist_ok=True)
            
            # Create archive filename
            archive_filename = f"financial_analysis_{year}_{quarter}.xlsx"
            archive_path = quarter_dir / archive_filename
            
            # Copy source file to archive
            if Path(source_file).exists():
                shutil.copy2(source_file, archive_path)
                logger.info(f"📁 Created quarterly archive: {archive_path}")
                return str(archive_path)
            else:
                logger.error(f"Source file not found: {source_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating quarterly archive: {e}")
            return None
    
    def get_quarterly_archives_info(self) -> Dict[str, Dict]:
        """Get information about existing quarterly archives."""
        if not self.archives_dir.exists():
            return {}
        
        archives_info = {}
        
        for quarter_dir in sorted(self.archives_dir.iterdir()):
            if quarter_dir.is_dir() and '_Q' in quarter_dir.name:
                try:
                    # Parse directory name (e.g., 2025_Q3)
                    year, quarter = quarter_dir.name.split('_Q')
                    quarter_key = f"Q{quarter}"
                    
                    # Find Excel files in this quarter
                    excel_files = list(quarter_dir.glob("financial_analysis_*.xlsx"))
                    
                    if excel_files:
                        latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
                        
                        archives_info[quarter_key] = {
                            "year": int(year),
                            "quarter": quarter_key,
                            "directory": str(quarter_dir),
                            "file_path": str(latest_file),
                            "last_modified": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                            "file_size": latest_file.stat().st_size,
                            "file_count": len(excel_files)
                        }
                        
                except Exception as e:
                    logger.warning(f"Error processing archive directory {quarter_dir.name}: {e}")
                    continue
        
        return archives_info
    
    def cleanup_old_exports(self, keep_days: int = 30) -> int:
        """Clean up old export files, keeping only recent ones."""
        logger.info(f"🧹 Cleaning up exports older than {keep_days} days...")
        
        if not self.excel_dir.exists():
            return 0
        
        cutoff_date = datetime.now().date() - timedelta(days=keep_days)
        cleaned_count = 0
        
        for excel_file in self.excel_dir.glob("financial_analysis_*.xlsx"):
            try:
                # Get file modification date
                file_date = datetime.fromtimestamp(excel_file.stat().st_mtime).date()
                
                if file_date < cutoff_date:
                    excel_file.unlink()
                    cleaned_count += 1
                    logger.info(f"🗑️  Cleaned up old file: {excel_file.name}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up {excel_file.name}: {e}")
                continue
        
        logger.info(f"✅ Cleaned up {cleaned_count} old export files")
        return cleaned_count
    
    def run_full_archive_process(self) -> Dict:
        """Run the complete archiving process."""
        logger.info("🚀 Starting full quarterly archiving process...")
        
        start_time = datetime.now()
        
        # Step 1: Archive existing exports
        archived_files = self.archive_existing_exports()
        
        # Step 2: Get archives info
        archives_info = self.get_quarterly_archives_info()
        
        # Step 3: Clean up old exports (optional)
        cleaned_count = self.cleanup_old_exports(keep_days=30)
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        summary = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "quarters_archived": len(archived_files),
            "total_archives": len(archives_info),
            "files_cleaned": cleaned_count,
            "archives_info": archives_info
        }
        
        logger.info("🎉 Quarterly archiving complete!")
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📁 Quarters archived: {len(archived_files)}")
        logger.info(f"📊 Total archives: {len(archives_info)}")
        logger.info(f"🧹 Files cleaned: {cleaned_count}")
        
        return summary

def main():
    """Main function to run the archiver."""
    archiver = QuarterlyArchiver()
    result = archiver.run_full_archive_process()
    
    if result["success"]:
        print("✅ Quarterly archiving completed successfully!")
        print(f"📁 Quarters archived: {result['quarters_archived']}")
        print(f"📊 Total archives: {result['total_archives']}")
        print(f"🧹 Files cleaned: {result['files_cleaned']}")
    else:
        print("❌ Quarterly archiving failed!")

if __name__ == "__main__":
    main()
