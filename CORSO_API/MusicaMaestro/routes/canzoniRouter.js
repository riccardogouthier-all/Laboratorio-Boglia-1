import express from 'express';
import { db } from '../server.js';
import { SELECT_ALL, SELECT_BY_ID, SELECT_BY_TITOLO,
         INSERT_CANZONE, UPDATE_CANZONE, DELETE_CANZONE } from '../database/script_canzoni.js';


const canzoniRouter = express.Router();


canzoniRouter.get("/", (req, res) => {
    console.log("GET /api/v2/canzoni");

    db.all(SELECT_ALL, (err, rows) => {
        if (err) {
            res.status(500).json({ error: err.message });
        } else {
            res.json(rows);
        }
    });
});

canzoniRouter.get("/search", (req, res) => {
    const titolo = req.query.titolo;
    console.log(`GET /api/v2/canzoni/search?titolo=${titolo}`);

    if (!titolo) {
        res.status(400).json({ error: "Parametro titolo non valido" });
        return;
    }

    db.all(SELECT_BY_TITOLO, [titolo], (err, rows) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        res.json(rows);
    });
});

canzoniRouter.get("/:id", (req, res) => {
    console.log(`GET /api/v2/canzoni/${req.params.id}`);

    db.get(SELECT_BY_ID, [req.params.id], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (row) {
            res.json(row);
        } else {
            res.status(404).json({ error: "Canzone non trovata" });
        }
    });
});

canzoniRouter.post("/", (req, res) => {
    console.log("POST /api/v2/canzoni");

    const errorMessage = validaCanzone(req.body);
    if (errorMessage) {
        res.status(400).json({ error: errorMessage });
        return;
    }

    const { titolo, artista, album, genere, durata_secondi } = req.body;

    db.run(INSERT_CANZONE, [titolo, artista, album, genere, durata_secondi], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else {
            res.status(201).json({ message: `Canzone inserita con ID ${this.lastID}` });
        }
    });
});

canzoniRouter.put("/:id", (req, res) => {
    console.log(`PUT /api/v2/canzoni/${req.params.id}`);

    const errorMessage = validaCanzone(req.body);
    if (errorMessage) {
        res.status(400).json({ error: errorMessage });
        return;
    }

    const id = req.params.id;
    const { titolo, artista, album, genere, durata_secondi } = req.body;

    db.run(UPDATE_CANZONE, [titolo, artista, album, genere, durata_secondi, id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes > 0) {
            res.json({ message: "Canzone aggiornata con successo" });
        } else {
            res.status(404).json({ error: "Canzone non trovata" });
        }
    });
});

canzoniRouter.delete("/:id", (req, res) => {
    const id = req.params.id;
    console.log(`DELETE /api/v2/canzoni/${id}`);

    db.run(DELETE_CANZONE, [id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes === 0) {
            res.status(404).json({ message: "Canzone non presente in database" });
        } else {
            res.json({ message: "Canzone cancellata con successo" });
        }
    });
});


/* UTILITY */
function validaCanzone(canzone) {
    if (!canzone) {
        return "Dati canzone non presenti";
    }
    if (!canzone.titolo || !canzone.artista || !canzone.album) {
        return "Titolo, artista e album sono obbligatori";
    }
    if (canzone.durata_secondi && isNaN(canzone.durata_secondi)) {
        return "La durata deve essere un numero (in secondi)";
    }
    return null;
}

export default canzoniRouter;
