# 🚀 ULTRA SIMPLE Checklist - Copy & Paste

Follow these steps EXACTLY. Should take 15-20 minutes.

---

## STEP 1: GitHub (5 minutes)

### A. Go to github.com
**Open**: https://github.com/signup

### B. Sign up
- Email: shadenone1@gmail.com
- Password: (create one, save it!)
- Username: (choose any, e.g., "shaden-deploy")
- Click "Create account"
- Verify email

### C. Create new repository
1. Click "+" (top right) → "New repository"
2. Name: `foreign-investment-tracker`
3. Check "Public"
4. DON'T initialize (no README, no .gitignore)
5. Click "Create repository"

### D. Copy the URL
You'll see: `https://github.com/YOUR-USERNAME/foreign-investment-tracker.git`
**Save this URL!**

---

## STEP 2: Push Code to GitHub (3 commands)

**Open Terminal** on your Mac

**Paste these 3 commands one by one**:

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

## STEP 3: Render (Backend) - 10 minutes

### A. Sign up
**Open**: https://render.com
1. Click "Get Started Free"
2. Sign up with GitHub (use "Continue with GitHub")
3. Click "Authorize Render"
4. Go to dashboard

### B. Deploy backend
1. Click "New +" → "Web Service"
2. Click "Connect GitHub repository"
3. Select: `YOUR-USERNAME/foreign-investment-tracker`
4. Configure:
   - **Name**: `foreign-investment-backend`
   - **Region**: Singapore (or closest)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --timeout 600 src.api.evidence_api:app`
5. Click "Create Web Service"
6. **WAIT 15-20 MINUTES** (be patient!)

### C. Get backend URL
When done, you'll see:
```
✅ Your service is live at: https://foreign-investment-backend.onrender.com
```

**Copy this URL!** Save it!

---

## STEP 4: Vercel (Frontend) - 5 minutes

### A. Sign up
**Open**: https://vercel.com
1. Click "Sign Up"
2. Sign up with GitHub
3. Click "Authorize Vercel"

### B. Deploy frontend
1. Click "Add New..." → "Project"
2. Import: `YOUR-USERNAME/foreign-investment-tracker`
3. Configure:
   - **Root Directory**: `frontend` (IMPORTANT!)
   - **Framework Preset**: Create React App (auto)
   - **Build Command**: `npm run build` (auto)
   - **Output Directory**: `build` (auto)
4. Click "Environment Variables" → "Add"
   - **Key**: `REACT_APP_API_URL`
   - **Value**: `https://foreign-investment-backend.onrender.com` (from Step 3!)
5. Click "Deploy"
6. **WAIT 3-5 MINUTES**

### C. Get frontend URL
When done, you'll see:
```
✅ Your site is live at: https://foreign-investment-tracker-xxxxx.vercel.app
```

**This is your LIVE URL!** 🎉

---

## STEP 5: Fix CORS (3 clicks)

1. Go back to **Render dashboard**
2. Click your backend service
3. Go to "Environment" tab
4. Click "Add Environment Variable":
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: `https://foreign-investment-tracker-xxxxx.vercel.app` (your Vercel URL!)
5. Click "Save Changes"
6. Wait 5 minutes for redeploy

---

## DONE! 🎉

**Your app is live**: `https://foreign-investment-tracker-xxxxx.vercel.app`

**Share this URL with your users!**

---

## Need Help?

**Copy the error message and ask me!**

