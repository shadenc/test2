# Quarterly Update System

This system automatically keeps your financial data up-to-date by coordinating all three scrapers and only processing new quarterly data.

## 🎯 What It Does

The Quarterly Update System automatically:

1. **Updates Foreign Ownership Data** - Gets latest company list from Tadawul
2. **Downloads New Financial PDFs** - Only downloads quarters you don't have
3. **Updates Net Profit Data** - Only scrapes new quarterly data
4. **Maintains Data Consistency** - Ensures all three sources stay synchronized

## 🏗️ System Architecture

```
Quarterly Update Orchestrator
    ↓
├── Foreign Ownership Scraper (ownership.py)
├── Financial PDF Downloader (hybrid_financial_downloader.py)
└── Net Profit Scraper (scrape_quarterly_net_profit.py)
    ↓
Frontend App (App.js) - Always up-to-date data
```

## 🚀 Quick Start

### 1. Run a Manual Update
```bash
# Run the orchestrator directly
python3 src/scrapers/quarterly_update_orchestrator.py

# Or use the scheduler
python3 src/scrapers/schedule_quarterly_updates.py --force
```

### 2. Check Update Status
```bash
python3 src/scrapers/schedule_quarterly_updates.py --status
```

### 3. Set Up Automated Updates
```bash
# Run the setup script
./src/scrapers/setup_cron_job.sh

# Or manually set frequency
python3 src/scrapers/schedule_quarterly_updates.py --frequency 7
```

## 📅 How It Works

### Smart Detection
- **PDFs**: Checks existing files before downloading
- **Net Profit**: Compares existing JSON data with available quarters
- **Ownership**: Updates company list if new companies are added

### Quarterly Logic
- **Q1 2025**: Downloads Q1 reports + Q4 2024 (Annual)
- **Q2 2025**: Downloads Q2 reports + Q1 reports
- **Q3 2025**: Downloads Q3 reports + Q2 reports
- **Q4 2025**: Downloads Q4 reports + Q3 reports

### Update Frequency
- **Default**: Every 7 days
- **Configurable**: Set custom intervals
- **Smart**: Only runs when updates are due

## 🛠️ Usage Examples

### Manual Updates
```bash
# Force run update (ignores schedule)
python3 src/scrapers/schedule_quarterly_updates.py --force

# Run if due (respects schedule)
python3 src/scrapers/schedule_quarterly_updates.py --run

# Check current status
python3 src/scrapers/schedule_quarterly_updates.py --status
```

### Configuration
```bash
# Set update frequency to every 3 days
python3 src/scrapers/schedule_quarterly_updates.py --frequency 3

# Disable auto-updates
python3 src/scrapers/schedule_quarterly_updates.py --disable-auto

# Enable auto-updates
python3 src/scrapers/schedule_quarterly_updates.py --enable-auto
```

### Cron Job Setup
```bash
# Interactive setup
./src/scrapers/setup_cron_job.sh

# Manual cron setup (every Monday at 2 AM)
0 2 * * 1 cd /path/to/project && python3 src/scrapers/schedule_quarterly_updates.py --run
```

## 📊 Monitoring & Logs

### Log Files
- **Main logs**: `quarterly_updates.log`
- **Cron logs**: `logs/cron_updates.log`
- **Update summaries**: `data/results/quarterly_update_summary.json`

### Schedule File
- **Location**: `data/quarterly_update_schedule.json`
- **Contains**: Last update time, next update, frequency, history

### Status Information
```bash
python3 src/scrapers/schedule_quarterly_updates.py --status
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the project root
   cd /path/to/project
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Browser Issues**
   ```bash
   # Check if Playwright is installed
   playwright install chromium
   ```

3. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x src/scrapers/*.py
   chmod +x src/scrapers/setup_cron_job.sh
   ```

### Debug Mode
```bash
# Run with verbose logging
python3 src/scrapers/quarterly_update_orchestrator.py 2>&1 | tee debug.log
```

## 📈 Performance

### Typical Update Times
- **Small update (1-2 companies)**: 5-10 minutes
- **Medium update (10-20 companies)**: 30-60 minutes
- **Full update (all companies)**: 2-4 hours

### Resource Usage
- **Memory**: ~500MB per browser instance
- **CPU**: Moderate during scraping
- **Network**: Varies by company count and PDF sizes

## 🔒 Security & Best Practices

### Rate Limiting
- Built-in delays between companies
- Random delays to avoid detection
- Respectful scraping practices

### Data Integrity
- Checksums for downloaded files
- Incremental updates only
- Backup of existing data before updates

### Error Handling
- Retry logic for failed requests
- Graceful degradation
- Comprehensive logging

## 🚀 Advanced Features

### Custom Schedules
```python
# Modify the scheduler for custom logic
class CustomScheduler(QuarterlyUpdateScheduler):
    def should_run_update(self):
        # Custom logic here
        pass
```

### Integration with External Systems
```python
# Hook into the update process
orchestrator = QuarterlyUpdateOrchestrator()
result = await orchestrator.run_quarterly_update()

# Send notifications, update databases, etc.
if result["success"]:
    send_slack_notification("Update completed successfully!")
```

### Monitoring & Alerts
```bash
# Check for failed updates
grep "❌" quarterly_updates.log

# Monitor update frequency
python3 src/scrapers/schedule_quarterly_updates.py --status
```

## 📚 API Reference

### QuarterlyUpdateOrchestrator

#### Methods
- `run_quarterly_update()` - Run complete update process
- `update_foreign_ownership_data()` - Update ownership data
- `update_financial_pdfs(symbols)` - Update PDFs for companies
- `update_net_profit_data(symbols)` - Update net profit data

#### Properties
- `current_year` - Current year
- `current_quarter` - Current quarter (Q1, Q2, Q3, Q4)
- `QUARTER_DATES` - Quarter end dates

### QuarterlyUpdateScheduler

#### Methods
- `run_scheduled_update()` - Run update if due
- `show_schedule_status()` - Display current status
- `set_frequency(days)` - Set update frequency
- `toggle_auto_update(enable)` - Enable/disable auto-updates

## 🎉 Benefits

1. **Always Fresh Data** - Your system stays current automatically
2. **Efficient Updates** - Only downloads what's new
3. **Consistent Data** - All three sources stay synchronized
4. **Automated** - Runs without manual intervention
5. **Configurable** - Adjust frequency and behavior as needed
6. **Monitored** - Track update history and performance
7. **Reliable** - Built-in retry logic and error handling

## 🔮 Future Enhancements

- **Web Dashboard** - Visual monitoring interface
- **Email Notifications** - Update completion alerts
- **Data Validation** - Automated quality checks
- **Performance Metrics** - Update speed and success rates
- **Integration APIs** - Connect with external systems

---

**Ready to get started?** Run `./src/scrapers/setup_cron_job.sh` to set up automated updates!
