#!/usr/bin/env python3
"""
Run Quarterly Archive Process
Manually run the quarterly archiving process to organize dashboard exports.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.quarterly_archiver import QuarterlyArchiver

def main():
    """Run the quarterly archiving process."""
    print("🚀 Starting Quarterly Archive Process")
    print("=" * 50)
    
    archiver = QuarterlyArchiver()
    result = archiver.run_full_archive_process()
    
    if result["success"]:
        print("\n✅ Quarterly archiving completed successfully!")
        print(f"📁 Quarters archived: {result['quarters_archived']}")
        print(f"📊 Total archives: {result['total_archives']}")
        print(f"🧹 Files cleaned: {result['files_cleaned']}")
        
        # Show archives info
        if result['archives_info']:
            print(f"\n📋 Archive Information:")
            for quarter, info in result['archives_info'].items():
                print(f"  {quarter}: {info['file_path']} ({info['file_size']} bytes)")
        
        print(f"\n📁 Archives directory: {archiver.archives_dir}")
        print(f"📊 Excel directory: {archiver.excel_dir}")
        
    else:
        print("\n❌ Quarterly archiving failed!")
        if 'error' in result:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
