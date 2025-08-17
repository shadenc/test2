#!/bin/bash
# Setup Quarterly Export Cron Job
# This script sets up automatic quarterly dashboard exports

echo "🚀 Setting up Automatic Quarterly Dashboard Exports"
echo "=================================================="

# Get the current project directory
PROJECT_DIR=$(pwd)
echo "📁 Project directory: $PROJECT_DIR"

# Create the cron job command
CRON_COMMAND="0 0 1 1,4,7,10 * cd $PROJECT_DIR && python3 simple_quarterly_export.py --auto"

echo "📅 Cron job will run:"
echo "   - January 1st (Q1)"
echo "   - April 1st (Q2)" 
echo "   - July 1st (Q3)"
echo "   - October 1st (Q4)"
echo ""

echo "⏰ Setting up cron job..."
echo "Current crontab:"
crontab -l 2>/dev/null || echo "No existing crontab"

echo ""
echo "Adding quarterly export job..."
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo ""
echo "✅ Cron job added successfully!"
echo ""
echo "📋 New crontab:"
crontab -l

echo ""
echo "🎯 What this does:"
echo "   - Automatically exports all available quarters"
echo "   - Creates quarterly archives"
echo "   - Runs at the start of each quarter"
echo ""
echo "🔧 To test manually:"
echo "   python3 simple_quarterly_export.py --auto"
echo ""
echo "🔧 To export specific quarter:"
echo "   python3 simple_quarterly_export.py --quarter Q1"
echo ""
echo "🔧 To remove cron job:"
echo "   crontab -e"
echo "   (then delete the line with simple_quarterly_export.py)"
