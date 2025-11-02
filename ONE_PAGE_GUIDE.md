# 🚀 Deploy Your App - One Page Guide

**Time**: 20-30 minutes | **Cost**: $0 | **Result**: Live URL for your users

---

## Quick Links
- GitHub: https://github.com/signup
- Render: https://render.com  
- Vercel: https://vercel.com

---

## Part 1: GitHub (5 min)

1. **Sign up**: github.com/signup
   - Email: shadenone1@gmail.com
   - Create password, choose username

2. **Create repo**:
   - Click "+" → "New repository"
   - Name: `foreign-investment-tracker`
   - Public, don't initialize anything
   - Create repository

3. **Push your code** (open Terminal, paste these):

```bash
cd "/Users/alangari/Downloads/SAMA/pool/clean/SAMA_projects/Finaical Statemnts/Foreign Investment Tracker"

git init
git add .
git commit -m "Ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/foreign-investment-tracker.git
git push -u origin main
```

**Replace** `YOUR-USERNAME` with your actual GitHub username!

---

## Part 2: Deploy Backend (Render) (15 min)

1. **Sign up**: render.com
   - Click "Continue with GitHub"
   - Authorize

2. **Deploy**:
   - "New +" → "Web Service"
   - Connect your repo
   - Settings:
     - Name: `foreign-investment-backend`
     - Build: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
     - Start: `gunicorn --bind 0.0.0.0:$PORT --timeout 600 src.api.evidence_api:app`
   - Create service

3. **Wait 15-20 minutes**, then **copy your URL**: `https://foreign-investment-backend.onrender.com`

---

## Part 3: Deploy Frontend (Vercel) (5 min)

1. **Sign up**: vercel.com
   - Sign up with GitHub

2. **Deploy**:
   - "Add New..." → "Project"  
   - Import your repo
   - **Root Directory**: `frontend` ⚠️
   - Add env var: `REACT_APP_API_URL` = your Render URL from Part 2
   - Deploy

3. **Copy your LIVE URL**: `https://foreign-investment-tracker-xxxxx.vercel.app` 🎉

---

## Part 4: Fix CORS (2 min)

1. Render dashboard → your backend
2. Environment → Add: `ALLOWED_ORIGINS` = your Vercel URL
3. Save, wait 5 minutes

---

## DONE! ✅

**Share your Vercel URL with users!**

**Need help? Ask me!**

