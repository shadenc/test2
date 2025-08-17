#!/usr/bin/env python3
"""
Quarterly Update Scheduler
Automatically runs quarterly updates at scheduled intervals.
Can be used with cron jobs or run manually.
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from quarterly_update_orchestrator import QuarterlyUpdateOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quarterly_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuarterlyUpdateScheduler:
    """Schedules and manages quarterly updates."""
    
    def __init__(self):
        self.orchestrator = QuarterlyUpdateOrchestrator()
        self.schedule_file = Path("data/quarterly_update_schedule.json")
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_schedule(self) -> dict:
        """Load the update schedule from file."""
        if not self.schedule_file.exists():
            # Default schedule
            default_schedule = {
                "last_update": None,
                "update_frequency_days": 7,  # Check weekly
                "next_update": None,
                "update_history": [],
                "auto_update": True
            }
            self.save_schedule(default_schedule)
            return default_schedule
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            return {"last_update": None, "update_frequency_days": 7, "next_update": None, "update_history": [], "auto_update": True}
    
    def save_schedule(self, schedule: dict):
        """Save the update schedule to file."""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
    
    def should_run_update(self) -> bool:
        """Check if an update should run based on schedule."""
        schedule = self.load_schedule()
        
        if not schedule.get("auto_update", True):
            logger.info("Auto-updates are disabled")
            return False
        
        if not schedule.get("next_update"):
            logger.info("No next update scheduled")
            return True
        
        next_update = datetime.fromisoformat(schedule["next_update"])
        now = datetime.now()
        
        if now >= next_update:
            logger.info("Update is due")
            return True
        
        logger.info(f"Next update scheduled for: {next_update}")
        return False
    
    def update_schedule(self, success: bool, duration: float):
        """Update the schedule after running an update."""
        schedule = self.load_schedule()
        
        now = datetime.now()
        schedule["last_update"] = now.isoformat()
        
        # Calculate next update
        frequency_days = schedule.get("update_frequency_days", 7)
        next_update = now + timedelta(days=frequency_days)
        schedule["next_update"] = next_update.isoformat()
        
        # Add to history
        update_record = {
            "timestamp": now.isoformat(),
            "success": success,
            "duration_seconds": duration,
            "companies_processed": 0  # Will be updated if available
        }
        
        schedule["update_history"].append(update_record)
        
        # Keep only last 10 updates
        if len(schedule["update_history"]) > 10:
            schedule["update_history"] = schedule["update_history"][-10:]
        
        self.save_schedule(schedule)
        
        logger.info(f"Schedule updated. Next update: {next_update}")
    
    async def run_scheduled_update(self) -> bool:
        """Run the scheduled update if it's due."""
        if not self.should_run_update():
            logger.info("No update due at this time")
            return False
        
        logger.info("🚀 Running scheduled quarterly update...")
        
        try:
            start_time = datetime.now()
            result = await self.orchestrator.run_quarterly_update()
            
            duration = (datetime.now() - start_time).total_seconds()
            success = result.get("success", False)
            
            # Update schedule
            self.update_schedule(success, duration)
            
            if success:
                logger.info("✅ Scheduled update completed successfully")
                return True
            else:
                logger.error("❌ Scheduled update failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during scheduled update: {e}")
            self.update_schedule(False, 0)
            return False
    
    def show_schedule_status(self):
        """Display the current schedule status."""
        schedule = self.load_schedule()
        
        print("\n📅 Quarterly Update Schedule Status")
        print("=" * 50)
        
        if schedule.get("last_update"):
            last_update = datetime.fromisoformat(schedule["last_update"])
            print(f"🕒 Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("🕒 Last Update: Never")
        
        if schedule.get("next_update"):
            next_update = datetime.fromisoformat(schedule["next_update"])
            now = datetime.now()
            if next_update > now:
                time_until = next_update - now
                print(f"⏰ Next Update: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏳ Time Until: {time_until.days} days, {time_until.seconds // 3600} hours")
            else:
                print(f"⏰ Next Update: {next_update.strftime('%Y-%m-%d %H:%M:%S')} (OVERDUE)")
        else:
            print("⏰ Next Update: Not scheduled")
        
        print(f"🔄 Update Frequency: Every {schedule.get('update_frequency_days', 7)} days")
        print(f"🤖 Auto Updates: {'Enabled' if schedule.get('auto_update', True) else 'Disabled'}")
        
        # Show recent history
        history = schedule.get("update_history", [])
        if history:
            print(f"\n📊 Recent Updates ({len(history)}):")
            for i, record in enumerate(history[-5:], 1):  # Show last 5
                timestamp = datetime.fromisoformat(record["timestamp"])
                status = "✅" if record["success"] else "❌"
                duration = record.get("duration_seconds", 0)
                print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M')} {status} ({duration:.0f}s)")
    
    def set_frequency(self, days: int):
        """Set the update frequency in days."""
        schedule = self.load_schedule()
        schedule["update_frequency_days"] = days
        
        # Recalculate next update
        if schedule.get("last_update"):
            last_update = datetime.fromisoformat(schedule["last_update"])
            next_update = last_update + timedelta(days=days)
            schedule["next_update"] = next_update.isoformat()
        
        self.save_schedule(schedule)
        logger.info(f"Update frequency set to every {days} days")
    
    def toggle_auto_update(self, enable: bool):
        """Enable or disable auto-updates."""
        schedule = self.load_schedule()
        schedule["auto_update"] = enable
        self.save_schedule(schedule)
        
        status = "enabled" if enable else "disabled"
        logger.info(f"Auto-updates {status}")

async def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Quarterly Update Scheduler")
    parser.add_argument("--run", action="store_true", help="Run the scheduled update if due")
    parser.add_argument("--force", action="store_true", help="Force run update regardless of schedule")
    parser.add_argument("--status", action="store_true", help="Show schedule status")
    parser.add_argument("--frequency", type=int, help="Set update frequency in days")
    parser.add_argument("--enable-auto", action="store_true", help="Enable auto-updates")
    parser.add_argument("--disable-auto", action="store_true", help="Disable auto-updates")
    parser.add_argument("--archive", action="store_true", help="Run quarterly archive process only")
    
    args = parser.parse_args()
    
    scheduler = QuarterlyUpdateScheduler()
    
    if args.status:
        scheduler.show_schedule_status()
        return
    
    if args.frequency:
        scheduler.set_frequency(args.frequency)
        return
    
    if args.enable_auto:
        scheduler.toggle_auto_update(True)
        return
    
    if args.disable_auto:
        scheduler.toggle_auto_update(False)
        return
    
    if args.archive:
        logger.info("📁 Running quarterly archive process...")
        try:
            from utils.quarterly_archiver import QuarterlyArchiver
            archiver = QuarterlyArchiver()
            result = archiver.run_full_archive_process()
            
            if result["success"]:
                print("✅ Quarterly archive completed successfully!")
                print(f"📁 Quarters archived: {result['quarters_archived']}")
                print(f"📊 Total archives: {result['total_archives']}")
            else:
                print("❌ Quarterly archive failed!")
        except Exception as e:
            print(f"❌ Error running archive: {e}")
        return
    
    if args.force:
        logger.info("🚀 Force running quarterly update...")
        orchestrator = QuarterlyUpdateOrchestrator()
        result = await orchestrator.run_quarterly_update()
        
        if result["success"]:
            print("✅ Force update completed successfully!")
        else:
            print("❌ Force update failed!")
        return
    
    if args.run:
        success = await scheduler.run_scheduled_update()
        if success:
            print("✅ Scheduled update completed successfully!")
        else:
            print("❌ Scheduled update failed or not due!")
        return
    
    # Default: show status
    scheduler.show_schedule_status()

if __name__ == "__main__":
    asyncio.run(main())
