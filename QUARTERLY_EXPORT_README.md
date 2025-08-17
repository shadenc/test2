# 🚀 Simple Quarterly Export System

## 🎯 What This Does

**Automatically exports dashboard data for each quarter** with the correct filters applied:

- **Q1 (Jan-Mar)**: Exports Q1 filtered data
- **Q2 (Apr-Jun)**: Exports Q2 filtered data  
- **Q3 (Jul-Sep)**: Exports Q3 filtered data
- **Q4 (Oct-Dec)**: Exports Q4 filtered data

## 🔧 How to Use

### **1. Export Current Quarter**
```bash
python3 simple_quarterly_export.py
```

### **2. Export Specific Quarter**
```bash
python3 simple_quarterly_export.py --quarter Q1
python3 simple_quarterly_export.py --quarter Q2
python3 simple_quarterly_export.py --quarter Q3
python3 simple_quarterly_export.py --quarter Q4
```

### **3. Export All Available Quarters**
```bash
python3 simple_quarterly_export.py --auto
```

### **4. Set Up Automatic Quarterly Exports**
```bash
./setup_quarterly_cron.sh
```

This will automatically run exports at the start of each quarter:
- **January 1st** (Q1)
- **April 1st** (Q2)
- **July 1st** (Q3)
- **October 1st** (Q4)

## 📁 What Gets Created

### **Excel Files**
```
output/excel/
├── dashboard_Q1_2025.xlsx
├── dashboard_Q2_2025.xlsx
├── dashboard_Q3_2025.xlsx
└── dashboard_Q4_2025.xlsx
```

### **Quarterly Archives**
```
output/archives/
├── 2025_Q1/
│   └── dashboard_Q1_2025.xlsx
├── 2025_Q2/
│   └── dashboard_Q2_2025.xlsx
├── 2025_Q3/
│   └── dashboard_Q3_2025.xlsx
└── 2025_Q4/
    └── dashboard_Q4_2025.xlsx
```

## 🎯 What Each Export Contains

Each Excel file contains:
- **Company symbols and names**
- **Foreign ownership data**
- **Retained earnings** (filtered by quarter)
- **Reinvested earnings** (filtered by quarter)
- **Net profit data** (filtered by quarter)
- **Quarter identifier**

## 🔄 How It Works

1. **Detects current quarter** automatically
2. **Loads data** from all three sources:
   - Foreign ownership data
   - Retained earnings flow data
   - Net profit data
3. **Applies quarter filter** to get relevant data
4. **Creates Excel export** with filtered data
5. **Archives** in quarterly folders
6. **Tracks** export history

## 🚨 Troubleshooting

### **If Export Fails**
- Check if data files exist in `data/` directory
- Ensure `output/` directory has write permissions
- Check console output for specific error messages

### **Manual Override**
If automatic exports fail, you can always run manually:
```bash
python3 simple_quarterly_export.py --auto
```

## 📊 Data Sources

The system uses these data files:
- `data/ownership/foreign_ownership_data.json`
- `data/results/retained_earnings_flow.csv`
- `data/results/quarterly_net_profit.json`

## 🎉 Benefits

- ✅ **Fully automated** quarterly exports
- ✅ **Correct filters** applied automatically
- ✅ **Organized archiving** by quarter
- ✅ **Consistent naming** convention
- ✅ **No manual intervention** required
- ✅ **Quarter-specific data** in each export

## 🔧 Customization

To add custom date ranges or filters, modify the `export_quarterly_dashboard()` function in `simple_quarterly_export.py`.

---

**That's it!** The system automatically handles quarterly exports with the correct filters applied.
