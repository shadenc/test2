# 🚀 Deploy Your App - Your Repo is Already Set Up!

**✅ Good News**: Your code is already on GitHub!

**Repo**: https://github.com/Innovation-Hub-Team/Saudi-Investment-Analyzer

---

## 🎯 Quick Deployment Steps

**Time**: 20 minutes | **Cost**: $0

---

## STEP 1: Deploy Backend on Render (15 min)

### A. Sign up
1. Go to: **https://render.com**
2. Click **"Get Started for Free"**
3. Click **"Continue with GitHub"**
4. Authorize Render

### B. Deploy your backend
1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect GitHub repository"**
3. Select: **`Innovation-Hub-Team/Saudi-Investment-Analyzer`**
4. Configure:
   - **Name**: `foreign-investment-backend`
   - **Region**: **Singapore** (closest to Saudi Arabia)
   - **Branch**: `main`
   - **Root Directory**: *(leave empty)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --timeout 600 src.api.evidence_api:app`
5. Scroll down and click **"Create Web Service"**
6. ⏳ **WAIT 15-20 MINUTES** (first build takes time)

### C. Get your backend URL
When it says **"Live"**, you'll see:
```
Your service is live at: https://foreign-investment-backend.onrender.com
```

**✅ Copy this URL!** You'll need it for Vercel!

---

## STEP 2: Deploy Frontend on Vercel (5 min)

### A. Sign up
1. Go to: **https://vercel.com**
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel

### B. Deploy your frontend
1. Click **"Add New..."** → **"Project"**
2. Find and import: **`Innovation-Hub-Team/Saudi-Investment-Analyzer`**
3. Configure:
   - **Framework Preset**: Create React App *(auto-detected)*
   - **Root Directory**: **`frontend`** ⚠️ **VERY IMPORTANT!**
   - **Build Command**: `npm run build` *(auto)*
   - **Output Directory**: `build` *(auto)*
4. Click **"Environment Variables"** → **"Add"**:
   - **Key**: `REACT_APP_API_URL`
   - **Value**: `https://foreign-investment-backend.onrender.com` *(from Step 1!)*
5. Click **"Deploy"**
6. ⏳ **WAIT 3-5 MINUTES**

### C. Get your frontend URL
When it says **"Ready"**, you'll see:
```
Your site is live at: https://saudi-investment-analyzer-xxxxx.vercel.app
```

**🎉 THIS IS YOUR LIVE URL!**

---

## STEP 3: Fix CORS (2 min)

1. Go back to **Render dashboard**
2. Click your **`foreign-investment-backend`** service
3. Click **"Environment"** tab
4. Click **"Add Environment Variable"**:
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: `https://saudi-investment-analyzer-xxxxx.vercel.app` *(your Vercel URL!)*
5. Click **"Save Changes"**
6. Wait 5 minutes for redeploy

---

## 🎉 DONE!

**Your app is live**: `https://saudi-investment-analyzer-xxxxx.vercel.app`

**Share this URL with your 4-10 users!**

---

## 🐛 Troubleshooting

### Render build fails?
- Check build logs in Render dashboard
- Make sure you selected `main` branch
- Playwright takes time, be patient!

### Vercel can't find files?
- Did you set **Root Directory** to `frontend`? ⚠️
- Check deployment logs

### Frontend can't connect to backend?
- Check `REACT_APP_API_URL` in Vercel settings
- Check `ALLOWED_ORIGINS` in Render settings
- Wait 5 minutes after changes

---

## ✅ Summary

**What you did:**
1. ✅ Connected Render to your GitHub repo
2. ✅ Deployed backend
3. ✅ Connected Vercel to same repo
4. ✅ Deployed frontend
5. ✅ Fixed CORS

**Result:**
- Live app for 4-10 users
- $0/month cost
- Professional URLs

---

## 📞 Need Help?

**If stuck, ask me! Share the error message and I'll help fix it.**

