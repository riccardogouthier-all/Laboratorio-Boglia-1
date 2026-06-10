import express from 'express';
import { db } from '../server.js';
import { SELECT_ALL_PLAYLIST, SELECT_PLAYLIST_BY_ID, INSERT_PLAYLIST, UPDATE_PLAYLIST, DELETE_PLAYLIST, SELECT_CANZONI_BY_PLAYLIST, INSERT_CANZONE_IN_PLAYLIST, DELETE_CANZONE_FROM_PLAYLIST,
} from '../database/script_playlist.js';

const playlistRouter = express.Router();

/* ─────────────────────────────────────────────
GET /api/playlist  →  tutte le playlist
───────────────────────────────────────────── */
playlistRouter.get('/', (req, res) => {
console.log('GET /api/playlist');
db.all(SELECT_ALL_PLAYLIST, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
});
});

/* ─────────────────────────────────────────────
GET /api/playlist/:id  →  singola playlist + canzoni
───────────────────────────────────────────── */
playlistRouter.get('/:id', (req, res) => {
console.log(`GET /api/playlist/${req.params.id}`);
db.get(SELECT_PLAYLIST_BY_ID, [req.params.id], (err, playlist) => {
    if (err)      return res.status(500).json({ error: err.message });
    if (!playlist) return res.status(404).json({ error: 'Playlist non trovata' });

    db.all(SELECT_CANZONI_BY_PLAYLIST, [req.params.id], (err2, songs) => {
    if (err2) return res.status(500).json({ error: err2.message });
    res.json({ ...playlist, songs: songs || [] });
    });
});
});

/* ─────────────────────────────────────────────
POST /api/playlist  →  crea nuova playlist
───────────────────────────────────────────── */
playlistRouter.post('/', (req, res) => {
console.log('POST /api/playlist');
const err = validaPlaylist(req.body);
if (err) return res.status(400).json({ error: err });

const { nome, descrizione } = req.body;
db.run(INSERT_PLAYLIST, [nome, descrizione ?? null], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.status(201).json({ message: `Playlist creata con ID ${this.lastID}`, id: this.lastID });
});
});

/* ─────────────────────────────────────────────
PUT /api/playlist/:id  →  sostituzione completa
───────────────────────────────────────────── */
playlistRouter.put('/:id', (req, res) => {
console.log(`PUT /api/playlist/${req.params.id}`);
const err = validaPlaylist(req.body);
if (err) return res.status(400).json({ error: err });

const { nome, descrizione } = req.body;
db.run(UPDATE_PLAYLIST, [nome, descrizione ?? null, req.params.id], function (err) {
    if (err)          return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Playlist non trovata' });
    res.json({ message: 'Playlist aggiornata con successo' });
});
});

/* ─────────────────────────────────────────────
PATCH /api/playlist/:id  →  aggiornamento parziale
───────────────────────────────────────────── */
playlistRouter.patch('/:id', (req, res) => {
console.log(`PATCH /api/playlist/${req.params.id}`);
const { nome, descrizione } = req.body;

if (nome === undefined && descrizione === undefined) {
    return res.status(400).json({ error: 'Nessun campo da aggiornare fornito (nome, descrizione)' });
}

  // Recupera i dati attuali e applica solo i campi presenti
db.get(SELECT_PLAYLIST_BY_ID, [req.params.id], (err, playlist) => {
    if (err)      return res.status(500).json({ error: err.message });
    if (!playlist) return res.status(404).json({ error: 'Playlist non trovata' });

    const nuovoNome = nome !== undefined ? nome : playlist.nome;
    const nuovaDesc = descrizione !== undefined ? descrizione : playlist.descrizione;

    db.run(UPDATE_PLAYLIST, [nuovoNome, nuovaDesc, req.params.id], function (err2) {
    if (err2) return res.status(500).json({ error: err2.message });
    res.json({ message: 'Playlist aggiornata parzialmente' });
    });
});
});

/* ─────────────────────────────────────────────
DELETE /api/playlist/:id  →  elimina playlist
───────────────────────────────────────────── */
playlistRouter.delete('/:id', (req, res) => {
console.log(`DELETE /api/playlist/${req.params.id}`);
db.run(DELETE_PLAYLIST, [req.params.id], function (err) {
    if (err)          return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Playlist non trovata' });
    res.json({ message: 'Playlist eliminata con successo' });
});
});

/* ─────────────────────────────────────────────
POST /api/playlist/:id/songs  →  aggiungi canzone
───────────────────────────────────────────── */
playlistRouter.post('/:id/songs', (req, res) => {
console.log(`POST /api/playlist/${req.params.id}/songs`);
const { song_id } = req.body;
if (!song_id) return res.status(400).json({ error: 'song_id è obbligatorio' });

db.run(INSERT_CANZONE_IN_PLAYLIST, [req.params.id, song_id], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.status(201).json({ message: 'Canzone aggiunta alla playlist' });
});
});

/* ─────────────────────────────────────────────
DELETE /api/playlist/:id/songs/:songId  →  rimuovi canzone
───────────────────────────────────────────── */
playlistRouter.delete('/:id/songs/:songId', (req, res) => {
console.log(`DELETE /api/playlist/${req.params.id}/songs/${req.params.songId}`);
db.run(DELETE_CANZONE_FROM_PLAYLIST, [req.params.id, req.params.songId], function (err) {
    if (err)          return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Associazione non trovata' });
    res.json({ message: 'Canzone rimossa dalla playlist' });
});
});

/* ─────────────────────────────────────────────
UTILITY
───────────────────────────────────────────── */
function validaPlaylist(body) {
if (!body) return 'Dati playlist non presenti';
if (!body.nome || body.nome.trim() === '') return 'Il campo nome è obbligatorio';
return null;
}

export default playlistRouter;