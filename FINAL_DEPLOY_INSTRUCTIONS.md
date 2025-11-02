# 🚀 FINAL DEPLOYMENT INSTRUCTIONS

## ✅ All Code is Ready!

I've prepared everything for deployment. Here's what's done:

1. ✅ **requirements.txt** - All dependencies added (Flask, Playwright, etc.)
2. ✅ **Procfile** - Render deployment config ready
3. ✅ **runtime.txt** - Python version set
4. ✅ **Frontend App.js** - All localhost URLs replaced with API_URL variable
5. ✅ **Backend CORS** - Fixed for production
6. ✅ **Gunicorn** - Configured for production server

---

## 🚀 Deployment Steps (30-60 minutes)

### STEP 1: Push to GitHub

```bash
# Navigate to your project
cd "/Users/alangari/Downloads/SAMA/pool/clean/SAMA_projects/Finaical Statemnts/Foreign Investment Tracker"

# Initialize git if needed
git init
git add .
git commit -m "Ready for deployment"

# Create a GitHub repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

### STEP 2: Deploy Backend on Render

**Visit**: https://render.com

1. **Sign up** for a free account
2. Click **"New +"** → **"Web Service"**
3. Connect your **GitHub** account
4. Select your repository
5. Configure:
   - **Name**: `foreign-investment-backend`
   - **Region**: Choose closest to Saudi Arabia
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --timeout 600 src.api.evidence_api:app`
6. Click **"Create Web Service"**
7. **Wait 15-20 minutes** for first build
8. **Copy your URL**: `https://your-app-name.onrender.com`

**Save this URL!** ✅

---

### STEP 3: Deploy Frontend on Vercel

**Visit**: https://vercel.com

1. **Sign up** for a free account  
2. Click **"New Project"**
3. Import your **GitHub** repository
4. Configure:
   - **Framework**: Create React App (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
5. **Add Environment Variable**:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://your-app-name.onrender.com` (from Step 2)
6. Click **"Deploy"**
7. **Wait 5 minutes**
8. **Copy your URL**: `https://your-app-name.vercel.app`

**This is your live URL!** 🎉

---

### STEP 4: Configure Backend CORS

1. Go back to **Render dashboard**
2. Click on your backend service
3. Go to **"Environment"** tab
4. Click **"Add Environment Variable"**:
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: `https://your-app-name.vercel.app`
5. **Save** and wait for redeploy (5 minutes)

---

### STEP 5: Keep Backend Awake (Optional)

Render free tier sleeps after 15 minutes. Keep it awake:

**Visit**: https://uptimerobot.com

1. **Sign up** (free)
2. Click **"+ Add New Monitor"**
3. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: My Backend
   - **URL**: `https://your-app-name.onrender.com/api/health`
   - **Interval**: 5 minutes
4. Click **"Create Monitor"**

**Backend stays awake 24/7!** ⚡

---

## 🎉 DONE!

**Your app is live at:**
- **Frontend**: `https://your-app-name.vercel.app`
- **Backend**: `https://your-app-name.onrender.com`

**Share the Vercel URL with your 4-10 users!**

---

## 🐛 Troubleshooting

### Build fails on Render:
- Check build logs in Render dashboard
- Make sure all dependencies are in requirements.txt
- Playwright takes time to install, be patient

### Frontend can't connect to backend:
- Check REACT_APP_API_URL in Vercel settings
- Verify ALLOWED_ORIGINS in Render settings
- Wait 5 minutes after changes for deployment

### Backend slow to respond:
- Normal for free tier after sleep
- Wait 10-30 seconds on first request
- Set up UptimeRobot to prevent sleep

### Evidence screenshots not showing:
- Check browser console for CORS errors
- Verify backend URL in frontend env variable

---

## 📞 Need Help?

1. Check logs in Render dashboard
2. Check logs in Vercel dashboard  
3. Come back and ask me!

---

## 💰 Cost

**Total**: **$0/month** (FREE forever!)

---

**Good luck! You've got this!** 🚀🎊

