@echo off
echo 🐳 Building AI Fashion Docker Image...
docker build -t ai-fashion .

echo ✅ Build complete! Starting container...
echo 📡 Your app will be available at: http://localhost:8000

docker run -p 8000:8000 -e DATABASE_URL="postgresql://fashion_jvy9_user:0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh@dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com/fashion_jvy9" ai-fashion
