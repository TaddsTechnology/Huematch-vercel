# 🚀 AI Fashion - Render Deployment Script
# This script prepares your app for Render deployment

Write-Host "🚀 Preparing AI Fashion for Render deployment..." -ForegroundColor Green

# 1. Copy lightweight files to root for Render
Write-Host "📦 Setting up deployment files..." -ForegroundColor Blue

# Copy main app file
Copy-Item -Path "backend\main.py" -Destination "main.py" -Force

# Copy requirements
Copy-Item -Path "backend\requirements.txt" -Destination "requirements.txt" -Force

# Copy runtime specification
if (Test-Path "runtime.txt") {
    Write-Host "✅ Runtime file exists" -ForegroundColor Green
} else {
    Write-Host "⚠️ Creating runtime.txt" -ForegroundColor Yellow
    "python-3.9.18" | Out-File -FilePath "runtime.txt" -Encoding UTF8
}

# Create Procfile for Render
Write-Host "📄 Creating Procfile..." -ForegroundColor Blue
"web: uvicorn main:app --host 0.0.0.0 --port $PORT" | Out-File -FilePath "Procfile" -Encoding UTF8

Write-Host "✅ Deployment files ready!" -ForegroundColor Green
Write-Host "" -ForegroundColor White

# Display file structure
Write-Host "📁 Your deployment structure:" -ForegroundColor Cyan
Write-Host "  ├── main.py (FastAPI app)" -ForegroundColor White
Write-Host "  ├── requirements.txt (lightweight deps)" -ForegroundColor White  
Write-Host "  ├── runtime.txt (Python 3.9)" -ForegroundColor White
Write-Host "  ├── Procfile (start command)" -ForegroundColor White
Write-Host "  └── frontend/ (for later Vercel deploy)" -ForegroundColor White

Write-Host "" -ForegroundColor White
Write-Host "🎯 Next steps:" -ForegroundColor Yellow
Write-Host "1. Push these files to your GitHub repository" -ForegroundColor White
Write-Host "2. Connect the repo to Render" -ForegroundColor White
Write-Host "3. Set environment variable: DATABASE_URL" -ForegroundColor White
Write-Host "4. Deploy! 🚀" -ForegroundColor White

Write-Host "" -ForegroundColor White
Write-Host "🔗 Render Dashboard: https://dashboard.render.com" -ForegroundColor Blue
