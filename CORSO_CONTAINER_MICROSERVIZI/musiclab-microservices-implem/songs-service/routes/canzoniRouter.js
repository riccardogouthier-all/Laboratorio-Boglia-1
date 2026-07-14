import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { db } from '../server.js';
import { publishEvent } from '../events/publisher.js';
import {
  SELECT_ALL, SELECT_BY_ID, SELECT_BY_FILTERS, SELECT_BY_TITOLO,
  INSERT_CANZONE, UPDATE_CANZONE, DELETE_CANZONE,
} from '../db/schema.js';

const canzoniRouter = express.Router();

const __dirname   = path.dirname(fileURLToPath(import.meta.url));
const AUDIO_DIR   = process.env.AUDIO_TRACKS_DIR || path.join(__dirname, '..', 'public', 'audio');

/* GET /api/canzoni?titolo=&artista= */
canzoniRouter.get('/', (req, res) => {
  const { titolo, artista } = req.query;
  if (titolo || artista) {
    db.all(SELECT_BY_FILTERS, { ':titolo': titolo ?? null, ':artista': artista ?? null }, (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(rows);
    });
  } else {
    db.all(SELECT_ALL, (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(rows);
    });
  }
});

/* GET /api/canzoni/search?titolo= */
canzoniRouter.get('/search', (req, res) => {
  const { titolo } = req.query;
  if (!titolo) return res.status(400).json({ error: 'Parametro titolo non valido' });
  db.all(SELECT_BY_TITOLO, [titolo], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

/* GET /api/canzoni/:id */
canzoniRouter.get('/:id', (req, res) => {
  db.get(SELECT_BY_ID, [req.params.id], (err, row) => {
    if (err)  return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Canzone non trovata' });
    res.json(row);
  });
});

/* GET /api/canzoni/:id/audio -> streaming del file audio associato */
canzoniRouter.get('/:id/audio', (req, res) => {
  db.get(SELECT_BY_ID, [req.params.id], (err, row) => {
    if (err)  return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Canzone non trovata' });
    if (!row.file_audio) return res.status(404).json({ error: 'Nessun file audio associato a questa canzone' });

    const filePath = path.join(AUDIO_DIR, row.file_audio);
    res.sendFile(filePath, (errSend) => {
      if (errSend && !res.headersSent) {
        res.status(404).json({ error: 'File audio non trovato sul server' });
      }
    });
  });
});

/* POST /api/canzoni */
canzoniRouter.post('/', (req, res) => {
  const errMsg = validaCanzone(req.body);
  if (errMsg) return res.status(400).json({ error: errMsg });

  const { titolo, artista, album, genere, anno, durata_secondi } = req.body;
  const file_audio = req.body.file_audio;

  db.run(INSERT_CANZONE, [titolo, artista, album ?? null, genere ?? null, anno ?? null, durata_secondi ?? null, file_audio], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    const nuovaCanzone = { id: this.lastID, titolo, artista, album, genere, anno, durata_secondi, file_audio };
    publishEvent('song.created', nuovaCanzone);
    res.status(201).json({ message: `Canzone inserita con ID ${this.lastID}`, id: this.lastID });
  });
});

/* PUT /api/canzoni/:id -> sostituzione completa */
canzoniRouter.put('/:id', (req, res) => {
  const errMsg = validaCanzone(req.body);
  if (errMsg) return res.status(400).json({ error: errMsg });

  db.get(SELECT_BY_ID, [req.params.id], (errGet, canzoneAttuale) => {
    if (errGet) return res.status(500).json({ error: errGet.message });
    if (!canzoneAttuale) return res.status(404).json({ error: 'Canzone non trovata' });

    const { titolo, artista, album, genere, anno, durata_secondi } = req.body;
    const file_audio = req.body.file_audio || canzoneAttuale.file_audio;

    db.run(UPDATE_CANZONE, [titolo, artista, album ?? null, genere ?? null, anno ?? null, durata_secondi ?? null, file_audio, req.params.id], function (err) {
      if (err)           return res.status(500).json({ error: err.message });
      if (!this.changes) return res.status(404).json({ error: 'Canzone non trovata' });
      publishEvent('song.updated', { id: Number(req.params.id), titolo, artista, album, genere, anno, durata_secondi, file_audio });
      res.json({ message: 'Canzone aggiornata con successo' });
    });
  });
});

/* PATCH /api/canzoni/:id -> aggiornamento parziale */
canzoniRouter.patch('/:id', (req, res) => {
  const campiConsentiti = ['titolo', 'artista', 'album', 'genere', 'anno', 'durata_secondi', 'file_audio'];
  const campiRicevuti   = Object.keys(req.body).filter(k => campiConsentiti.includes(k));
  if (campiRicevuti.length === 0) return res.status(400).json({ error: 'Nessun campo valido da aggiornare' });

  db.get(SELECT_BY_ID, [req.params.id], (err, canzone) => {
    if (err)      return res.status(500).json({ error: err.message });
    if (!canzone) return res.status(404).json({ error: 'Canzone non trovata' });

    const updated = {
      titolo:         req.body.titolo         ?? canzone.titolo,
      artista:        req.body.artista        ?? canzone.artista,
      album:          req.body.album          ?? canzone.album,
      genere:         req.body.genere         ?? canzone.genere,
      anno:           req.body.anno           ?? canzone.anno,
      durata_secondi: req.body.durata_secondi ?? canzone.durata_secondi,
      file_audio:     req.body.file_audio     ?? canzone.file_audio,
    };

    db.run(
      UPDATE_CANZONE,
      [updated.titolo, updated.artista, updated.album, updated.genere, updated.anno, updated.durata_secondi, updated.file_audio, req.params.id],
      function (err2) {
        if (err2) return res.status(500).json({ error: err2.message });
        publishEvent('song.updated', { id: Number(req.params.id), ...updated });
        res.json({ message: 'Canzone aggiornata parzialmente' });
      }
    );
  });
});

/* DELETE /api/canzoni/:id */
canzoniRouter.delete('/:id', (req, res) => {
  db.run(DELETE_CANZONE, [req.params.id], function (err) {
    if (err)           return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Canzone non trovata' });
    publishEvent('song.deleted', { id: Number(req.params.id) });
    res.json({ message: 'Canzone cancellata con successo' });
  });
});

function validaCanzone(body) {
  if (!body) return 'Dati canzone non presenti';
  if (!body.titolo || !body.artista) return 'Titolo e artista sono obbligatori';
  if (body.durata_secondi && isNaN(body.durata_secondi)) return 'La durata deve essere un numero (in secondi)';
  if (body.anno && isNaN(body.anno)) return "L'anno deve essere un numero";
  return null;
}

export default canzoniRouter;
