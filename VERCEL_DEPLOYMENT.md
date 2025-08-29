# AI Fashion - Complete Vercel Deployment Guide

This guide covers deploying both your React frontend and FastAPI backend on Vercel.

## 🚀 Quick Deployment Steps

### 1. Prerequisites
- GitHub account
- Vercel account (free tier works fine)
- Your project pushed to GitHub

### 2. Deploy to Vercel

#### Option A: Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to your project
cd "C:\Users\s kabariya\desktop\New folder\Ai-Fashion"

# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel --prod
```

#### Option B: Vercel Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Click "Import Project"
3. Connect your GitHub repository
4. Select your AI-Fashion repository
5. Vercel will auto-detect the configuration

### 3. Environment Variables
In your Vercel dashboard, add these environment variables:

```
DATABASE_URL=your_postgresql_connection_string
VITE_API_URL=https://your-app.vercel.app
```

## 📁 Project Structure (After Setup)

```
Ai-Fashion/
├── api/                          # Vercel serverless functions
│   ├── index.py                 # Main API handler
│   ├── health.py               # Health check endpoint
│   ├── color-recommendations.py # Color API
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React application
│   ├── src/
│   ├── package.json
│   └── dist/                   # Build output
├── backend/                    # Original backend (for reference)
└── vercel.json                # Vercel configuration
```

## 🔧 Configuration Files Explained

### vercel.json
- Configures both frontend build and API functions
- Routes API calls to `/api/*` endpoints
- Serves React app for all other routes

### api/requirements.txt
- Lightweight dependencies for Vercel limits
- Core FastAPI and database packages only

### Updated Frontend API Config
- Automatically detects Vercel environment
- Uses relative API paths in production
- Falls back to localhost in development

## 📡 API Endpoints

After deployment, your APIs will be available at:

- **Health Check**: `https://your-app.vercel.app/api/health`
- **Color Recommendations**: `https://your-app.vercel.app/api/color-recommendations`
- **Main API**: `https://your-app.vercel.app/api/`

## 🐛 Troubleshooting

### Common Issues:

1. **Build Fails**
   ```bash
   # Clear node modules and rebuild
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

2. **API Timeout**
   - Vercel free tier has 10s function timeout
   - Reduce database query complexity
   - Add caching for expensive operations

3. **Database Connection Issues**
   - Ensure DATABASE_URL is set correctly
   - Check if database allows connections from Vercel IPs
   - Consider connection pooling

4. **CORS Issues**
   ```python
   # API functions include permissive CORS:
   allow_origins=["*"]  # Vercel-specific
   ```

## 🔄 Development Workflow

### Local Development
```bash
# Frontend
cd frontend
npm run dev

# Backend (separate terminal)
cd backend
python main.py
```

### Deploy Changes
```bash
# Auto-deploy via GitHub (if connected)
git add .
git commit -m "Update application"
git push origin main

# Manual deploy
vercel --prod
```

## 📊 Monitoring

### Check Deployment Status
- Visit your Vercel dashboard
- Monitor function logs
- Check build logs

### API Health
```bash
# Test your deployed API
curl https://your-app.vercel.app/api/health
```

## 💡 Performance Tips

1. **Frontend Optimization**
   - Bundle splitting configured in Vite
   - Static assets cached by Vercel CDN
   - Code splitting for better loading

2. **Backend Optimization**
   - Lightweight dependencies
   - Connection pooling for database
   - Caching for repeated queries

3. **Database Optimization**
   - Index frequently queried columns
   - Limit result sets
   - Use pagination

## 🔒 Security Notes

- Environment variables are secure in Vercel
- API endpoints have CORS configured
- Database credentials not exposed to frontend

## 📈 Scaling Considerations

### Vercel Limits (Free Tier)
- 100GB bandwidth/month
- 10s function timeout
- 1000 serverless function invocations/day

### Upgrade Path
- Pro plan for higher limits
- Consider separating database-heavy operations
- Implement caching layer (Redis)

## 🛠️ Next Steps

1. **Custom Domain** (optional)
   - Add your domain in Vercel dashboard
   - Update DNS settings

2. **Analytics** (optional)
   - Enable Vercel Analytics
   - Add error tracking (Sentry)

3. **CI/CD** (recommended)
   - Connect GitHub for auto-deployment
   - Set up staging environment

## 📞 Support

- **Vercel Docs**: https://vercel.com/docs
- **FastAPI + Vercel**: https://vercel.com/docs/functions/serverless-functions/runtimes/python
- **React + Vercel**: https://vercel.com/docs/frameworks/vite

---

✅ **Deployment Complete!** Your AI Fashion app is now live on Vercel with both frontend and backend functionality.
