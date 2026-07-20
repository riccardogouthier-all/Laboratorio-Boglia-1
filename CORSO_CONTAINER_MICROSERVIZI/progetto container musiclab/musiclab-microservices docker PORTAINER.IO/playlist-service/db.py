import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/playlist.db")

CREATE_PLAYLIST_TABLE = """
CREATE TABLE IF NOT EXISTS playlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    descrizione TEXT
)
"""

CREATE_PLAYLIST_CANZONI_TABLE = """
CREATE TABLE IF NOT EXISTS playlist_canzoni (
    playlist_id INTEGER NOT NULL,
    canzone_id  INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, canzone_id),
    FOREIGN KEY (playlist_id) REFERENCES playlist(id) ON DELETE CASCADE
)
"""

# Cache locale delle canzoni, sincronizzata via RabbitMQ dal songs-service.
# In un'architettura a microservizi ogni servizio possiede il proprio
# database: qui non facciamo mai una JOIN diretta sul DB del songs-service.
CREATE_CANZONI_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS canzoni_cache (
    id      INTEGER PRIMARY KEY,
    titolo  TEXT,
    artista TEXT,
    album   TEXT
)
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(CREATE_PLAYLIST_TABLE)
    conn.execute(CREATE_PLAYLIST_CANZONI_TABLE)
    conn.execute(CREATE_CANZONI_CACHE_TABLE)
    conn.commit()
    conn.close()
