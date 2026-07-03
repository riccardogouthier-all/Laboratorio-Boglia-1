from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_connection

router = APIRouter(prefix="/api/playlist", tags=["Playlist"])


class NuovaPlaylist(BaseModel):
    nome: str
    descrizione: Optional[str] = None


class PatchPlaylist(BaseModel):
    nome: Optional[str] = None
    descrizione: Optional[str] = None


class AggiungiCanzone(BaseModel):
    song_id: int


def _playlist_to_dict(row) -> dict:
    return {"id": row["id"], "nome": row["nome"], "descrizione": row["descrizione"]}


def _get_songs_for_playlist(conn, playlist_id: int):
    rows = conn.execute(
        """
        SELECT cc.id, cc.titolo, cc.artista, cc.album
        FROM canzoni_cache cc
        JOIN playlist_canzoni pc ON cc.id = pc.canzone_id
        WHERE pc.playlist_id = ?
        """,
        (playlist_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("")
def get_all_playlists():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM playlist").fetchall()
        return [_playlist_to_dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/{playlist_id}")
def get_playlist(playlist_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM playlist WHERE id = ?", (playlist_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Playlist non trovata")
        result = _playlist_to_dict(row)
        result["songs"] = _get_songs_for_playlist(conn, playlist_id)
        return result
    finally:
        conn.close()


@router.post("", status_code=201)
def create_playlist(body: NuovaPlaylist):
    if not body.nome or not body.nome.strip():
        raise HTTPException(status_code=400, detail="Il campo nome è obbligatorio")
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO playlist (nome, descrizione) VALUES (?, ?)",
            (body.nome, body.descrizione),
        )
        conn.commit()
        return {"message": f"Playlist creata con ID {cur.lastrowid}", "id": cur.lastrowid}
    finally:
        conn.close()


@router.put("/{playlist_id}")
def update_playlist(playlist_id: int, body: NuovaPlaylist):
    if not body.nome or not body.nome.strip():
        raise HTTPException(status_code=400, detail="Il campo nome è obbligatorio")
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE playlist SET nome = ?, descrizione = ? WHERE id = ?",
            (body.nome, body.descrizione, playlist_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Playlist non trovata")
        return {"message": "Playlist aggiornata con successo"}
    finally:
        conn.close()


@router.patch("/{playlist_id}")
def patch_playlist(playlist_id: int, body: PatchPlaylist):
    if body.nome is None and body.descrizione is None:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare fornito (nome, descrizione)")
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM playlist WHERE id = ?", (playlist_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Playlist non trovata")
        nuovo_nome = body.nome if body.nome is not None else row["nome"]
        nuova_desc = body.descrizione if body.descrizione is not None else row["descrizione"]
        conn.execute(
            "UPDATE playlist SET nome = ?, descrizione = ? WHERE id = ?",
            (nuovo_nome, nuova_desc, playlist_id),
        )
        conn.commit()
        return {"message": "Playlist aggiornata parzialmente"}
    finally:
        conn.close()


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int):
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM playlist WHERE id = ?", (playlist_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Playlist non trovata")
        return {"message": "Playlist eliminata con successo"}
    finally:
        conn.close()


@router.post("/{playlist_id}/songs", status_code=201)
def add_song_to_playlist(playlist_id: int, body: AggiungiCanzone):
    conn = get_connection()
    try:
        playlist = conn.execute("SELECT id FROM playlist WHERE id = ?", (playlist_id,)).fetchone()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist non trovata")
        conn.execute(
            "INSERT OR IGNORE INTO playlist_canzoni (playlist_id, canzone_id) VALUES (?, ?)",
            (playlist_id, body.song_id),
        )
        conn.commit()
        return {"message": "Canzone aggiunta alla playlist"}
    finally:
        conn.close()


@router.delete("/{playlist_id}/songs/{song_id}")
def remove_song_from_playlist(playlist_id: int, song_id: int):
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM playlist_canzoni WHERE playlist_id = ? AND canzone_id = ?",
            (playlist_id, song_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Associazione non trovata")
        return {"message": "Canzone rimossa dalla playlist"}
    finally:
        conn.close()
