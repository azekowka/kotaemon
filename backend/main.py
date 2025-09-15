from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, files

app = FastAPI(
    title="Kotaemon API",
    description="API server for Kotaemon",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(files.router)

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}
