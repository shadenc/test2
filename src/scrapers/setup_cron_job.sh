#!/bin/bash
# Setup Cron Job for Quarterly Updates
# This script helps set up automated quarterly updates

echo "🚀 Setting up Cron Job for Quarterly Updates"
echo "=============================================="

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Script directory: $SCRIPT_DIR"

# Create the cron job command
CRON_COMMAND="0 2 * * 1 cd $PROJECT_ROOT && python3 src/scrapers/schedule_quarterly_updates.py --run >> logs/cron_updates.log 2>&1"

echo ""
echo "📅 Cron job command:"
echo "$CRON_COMMAND"
echo ""

echo "⏰ This will run every Monday at 2:00 AM"
echo "🔄 It will check if updates are due and run them automatically"
echo "📝 Logs will be saved to logs/cron_updates.log"
echo ""

# Ask user if they want to install the cron job
read -p "Do you want to install this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
    
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📋 Current cron jobs:"
    crontab -l
    
    echo ""
    echo "🔧 To manage the cron job:"
    echo "   - Edit: crontab -e"
    echo "   - List: crontab -l"
    echo "   - Remove: crontab -r"
    echo ""
    echo "📊 To check update status manually:"
    echo "   python3 src/scrapers/schedule_quarterly_updates.py --status"
    echo ""
    echo "🚀 To force run an update:"
    echo "   python3 src/scrapers/schedule_quarterly_updates.py --force"
    
else
    echo "❌ Cron job not installed."
    echo ""
    echo "💡 You can manually run updates using:"
    echo "   python3 src/scrapers/schedule_quarterly_updates.py --run"
    echo ""
    echo "📊 Or check status with:"
    echo "   python3 src/scrapers/schedule_quarterly_updates.py --status"
fi

echo ""
echo "🎯 The system will now automatically keep your data up-to-date!"
echo "   - Foreign ownership data"
echo "   - Financial statement PDFs"
echo "   - Quarterly net profit data"
