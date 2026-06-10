import express from 'express';
import { db } from '../server.js';
import { SELECT_ALL, SELECT_BY_ID, SELECT_BY_FILTERS, SELECT_BY_TITOLO, INSERT_CANZONE, UPDATE_CANZONE, DELETE_CANZONE,
} from '../database/script_canzoni.js';

const canzoniRouter = express.Router();

/* ─────────────────────────────────────────────
GET /api/canzoni?titolo=&artista=
───────────────────────────────────────────── */
canzoniRouter.get('/', (req, res) => {
const { titolo, artista } = req.query;
console.log(`GET /api/canzoni titolo=${titolo} artista=${artista}`);

if (titolo || artista) {
    db.all(
    SELECT_BY_FILTERS,
    { ':titolo': titolo ?? null, ':artista': artista ?? null },
    (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(rows);
    }
    );
} else {
    db.all(SELECT_ALL, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
    });
}
});

/* ─────────────────────────────────────────────
GET /api/canzoni/search?titolo=
───────────────────────────────────────────── */
canzoniRouter.get('/search', (req, res) => {
const { titolo } = req.query;
console.log(`GET /api/canzoni/search?titolo=${titolo}`);
if (!titolo) return res.status(400).json({ error: 'Parametro titolo non valido' });

db.all(SELECT_BY_TITOLO, [titolo], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
});
});

/* ─────────────────────────────────────────────
GET /api/canzoni/:id
───────────────────────────────────────────── */
canzoniRouter.get('/:id', (req, res) => {
console.log(`GET /api/canzoni/${req.params.id}`);
db.get(SELECT_BY_ID, [req.params.id], (err, row) => {
    if (err)  return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Canzone non trovata' });
    res.json(row);
});
});

/* ─────────────────────────────────────────────
POST /api/canzoni
───────────────────────────────────────────── */
canzoniRouter.post('/', (req, res) => {
console.log('POST /api/canzoni');
const errMsg = validaCanzone(req.body);
if (errMsg) return res.status(400).json({ error: errMsg });

const { titolo, artista, album, genere, anno, durata_secondi } = req.body;
db.run(INSERT_CANZONE, [titolo, artista, album ?? null, genere ?? null, anno ?? null, durata_secondi ?? null], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.status(201).json({ message: `Canzone inserita con ID ${this.lastID}`, id: this.lastID });
});
});

/* ─────────────────────────────────────────────
PUT /api/canzoni/:id  →  sostituzione completa
───────────────────────────────────────────── */
canzoniRouter.put('/:id', (req, res) => {
console.log(`PUT /api/canzoni/${req.params.id}`);
const errMsg = validaCanzone(req.body);
if (errMsg) return res.status(400).json({ error: errMsg });

const { titolo, artista, album, genere, anno, durata_secondi } = req.body;
db.run(
    UPDATE_CANZONE,
    [titolo, artista, album ?? null, genere ?? null, anno ?? null, durata_secondi ?? null, req.params.id],
    function (err) {
    if (err)          return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Canzone non trovata' });
    res.json({ message: 'Canzone aggiornata con successo' });
    }
);
});

/* ─────────────────────────────────────────────
PATCH /api/canzoni/:id  →  aggiornamento parziale
───────────────────────────────────────────── */
canzoniRouter.patch('/:id', (req, res) => {
console.log(`PATCH /api/canzoni/${req.params.id}`);
const campiConsentiti = ['titolo', 'artista', 'album', 'genere', 'anno', 'durata_secondi'];
const campiRicevuti   = Object.keys(req.body).filter(k => campiConsentiti.includes(k));

if (campiRicevuti.length === 0) {
    return res.status(400).json({ error: 'Nessun campo valido da aggiornare' });
}

  // Legge il record attuale e applica solo i campi presenti
db.get(SELECT_BY_ID, [req.params.id], (err, canzone) => {
    if (err)     return res.status(500).json({ error: err.message });
    if (!canzone) return res.status(404).json({ error: 'Canzone non trovata' });

    const updated = {
    titolo:         req.body.titolo         !== undefined ? req.body.titolo         : canzone.titolo,
    artista:        req.body.artista        !== undefined ? req.body.artista        : canzone.artista,
    album:          req.body.album          !== undefined ? req.body.album          : canzone.album,
    genere:         req.body.genere         !== undefined ? req.body.genere         : canzone.genere,
    anno:           req.body.anno           !== undefined ? req.body.anno           : canzone.anno,
    durata_secondi: req.body.durata_secondi !== undefined ? req.body.durata_secondi : canzone.durata_secondi,
    };

    db.run(
    UPDATE_CANZONE,
    [updated.titolo, updated.artista, updated.album, updated.genere, updated.anno, updated.durata_secondi, req.params.id],
    function (err2) {
        if (err2) return res.status(500).json({ error: err2.message });
        res.json({ message: 'Canzone aggiornata parzialmente' });
        }
    );
});
});

/* ─────────────────────────────────────────────
DELETE /api/canzoni/:id
───────────────────────────────────────────── */
canzoniRouter.delete('/:id', (req, res) => {
console.log(`DELETE /api/canzoni/${req.params.id}`);
db.run(DELETE_CANZONE, [req.params.id], function (err) {
    if (err)          return res.status(500).json({ error: err.message });
    if (!this.changes) return res.status(404).json({ error: 'Canzone non trovata' });
    res.json({ message: 'Canzone cancellata con successo' });
});
});

/* ─────────────────────────────────────────────
UTILITY
───────────────────────────────────────────── */
function validaCanzone(body) {
if (!body) return 'Dati canzone non presenti';
if (!body.titolo || !body.artista) return 'Titolo e artista sono obbligatori';
if (body.durata_secondi && isNaN(body.durata_secondi)) return 'La durata deve essere un numero (in secondi)';
if (body.anno && isNaN(body.anno)) return 'L\'anno deve essere un numero';
return null;
}

export default canzoniRouter;