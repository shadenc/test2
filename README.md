# Foreign Investment Analysis System

## Quick Start

### Local Development
```bash
python start_system.py
```

### Deploy to Production (FREE!)
**Your repo is ready!** Follow:
- **🚀 QUICK START**: `YOUR_REPO_DEPLOY.md` - Deploy in 20 minutes (recommended!)
- **📖 Detailed**: `FINAL_DEPLOY_INSTRUCTIONS.md` - Full step-by-step guide
- **💡 Learn More**: `HONEST_DEPLOYMENT_GUIDE.md` - All hosting options explained

## Project Overview

This system tracks foreign investment flows in Saudi stock market companies by analyzing quarterly financial statements.

**Tech Stack:**
- Backend: Python Flask + Playwright
- Frontend: React + Material-UI
- Data: JSON, CSV, SQLite

**Features:**
- Foreign ownership data scraping from Tadawul
- Quarterly financial PDF downloads
- Retained earnings extraction with evidence screenshots
- Net profit data collection
- Financial flow calculations
- Excel exports with Arabic RTL support
- Background job processing
- Real-time progress tracking

## File Structure

```
├── src/
│   ├── api/              # Flask backend API
│   ├── scrapers/         # Web scrapers (ownership, PDFs, net profit)
│   ├── extractors/       # PDF data extraction
│   ├── calculators/      # Financial calculations
│   └── utils/            # Utilities (Excel export, screenshots)
├── frontend/             # React frontend
├── data/                 # Data storage (PDFs, results, ownership)
├── output/               # Generated files (screenshots, exports, archives)
├── requirements.txt      # Python dependencies
├── Procfile              # Production deployment config
└── runtime.txt           # Python version
```

## Requirements

- Python 3.12+
- Node.js 14+
- Playwright browser automation
- Internet connection for data scraping

## Deployment Options

### FREE Options:
1. **Render Free + Vercel Free** ($0/month) - May sleep
2. **Fly.io Free + Vercel Free** ($0/month) - May sleep  
3. **VPS** (~$4-6/month) - Always on, more control

### Recommended:
**Render + Vercel** ($0/month), absolutely free!

See deployment guides for setup instructions.
