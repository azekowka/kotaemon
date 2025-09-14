from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_application
from .routers import chat, files # Import the new routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_instance = get_application()
    app_instance.register_reasonings()
    app_instance.initialize_indices()
    yield

app = FastAPI(lifespan=lifespan)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # Your Next.js frontend origin
    # Add other origins if your frontend is deployed elsewhere
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Kotaemon FastAPI server is running"}

# Include routers for different functionalities
app.include_router(chat.router)
app.include_router(files.router)
