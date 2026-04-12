from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.api.profiler import router as profiler_router

app = FastAPI(title="Talk2Data Execution Engine")

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://natwest-hackathon-backend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers
app.include_router(router)
app.include_router(profiler_router)

@app.get("/")
def home():
    return {"message": "Execution Engine running"}