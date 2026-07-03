from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from events.consumer import start_consumer_thread
from routers.playlist import router as playlist_router

app = FastAPI(
    title="MusicLab - Playlist Service API",
    description="Microservizio per la gestione delle playlist (Python/FastAPI)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(playlist_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "playlist-service"}


@app.on_event("startup")
def on_startup():
    init_db()
    start_consumer_thread()
