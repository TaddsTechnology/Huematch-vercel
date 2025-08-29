from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
def health_check():
    return JSONResponse({
        "status": "healthy",
        "message": "AI Fashion API is running on Vercel",
        "platform": "vercel"
    })

# Export for Vercel
handler = app
