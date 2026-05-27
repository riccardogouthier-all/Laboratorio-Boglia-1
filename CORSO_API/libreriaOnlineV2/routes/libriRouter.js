import express from 'express';
import { db } from '../server.js';
import {SELECT_ALL, SELECT_BY_ID, SELECT_BY_TITOLO, SELECT_ALL_ID,
        INSERT_LIBRO, UPDATE_LIBRO, DELETE_LIBRO} from '../database/script_libri.js';


const libriRouter = express.Router();


libriRouter.get("/", (req, res) => {            // SELECT ALL
    console.log("GET /api/v2/libri");

    db.all(SELECT_ALL, (err, rows) => {
        if (err) {
            res.status(500).json({ error: message });
        } else {
            res.json(rows);
        }
    });
});

libriRouter.get("/id", (req, res) => {            // SELECT ALL ID
    console.log("GET /api/v2/libri/id");

    db.all(SELECT_ALL_ID, (err, rows) => {
        if (err) {
            res.status(500).json({ error: message });
        } else {
            res.json(rows);
        }
    });
});

libriRouter.get("/search", (req, res) => {            // SELECT BY TITOLO
    console.log(`GET /api/v2/libri/search?titolo=${req.query.titolo}`);

    db.all(SELECT_BY_TITOLO, [req.query.titolo], (err, rows) => {
        if (err) {
            res.status(500).json({ error: message });
        } else if (rows) {
            res.json(rows);
        } else {
            res.status(404).json({ message: `Libro con titolo ${titolo} non trovato` });
        }
    });
});

libriRouter.get("/:id", (req, res) => {            // SELECT BY ID
    console.log(`GET /api/v2/libri/${req.params.id}`);
    console.log("search by id");

    db.all(SELECT_BY_ID, [req.params.id], (err, rows) => {
        if (err) {
            res.status(500).json({ error: message });
        } else if (rows) {
            res.json(rows);
        } else {
            res.status(404).json({ message: `Libro con ID ${id} non trovato` });
        }
    });
});


libriRouter.post("/", (req, res) => {               // INSERT NUOVO LIBRO
    console.log("POST /api/v2/libri", req.body)

    // controllo che il body esista
    const errorMessage = validaLibro(req.body);
    if (errorMessage) {
        res.status(400).json({ error: errorMessage });
        return;
    }

    // estraggo le proprietà dal body
    const { titolo, autore, editore, genere, numero_pagine } = req.body;
    
    db.run(INSERT_LIBRO, [titolo, autore, editore, genere, numero_pagine], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else {
            res.status(201).json({ message: `Libro inserito con ID ${this.lastID}` });
        }
    });
});

libriRouter.put("/:id", (req, res) => {             // UPDATE AGGIORNA LIBRO
    console.log(`PUT /api/v2/libri/${req.params.id}`);

    const errorMessage = validaLibro(req.body);
    if (errorMessage) {
        res.status(400).json({ error: errorMessage });
        return;
    }

    const id = req.params.id;
    const { titolo, autore, editore, genere, numero_pagine } = req.body;

    db.run(UPDATE_LIBRO, [titolo, autore, editore, genere, numero_pagine, id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes > 0) {
            res.json({ message: `Libro con ID ${id} aggiornato` });
        } else {
            res.status(404).json({ message: "Libro non trovato" });
        }   

    });
});

libriRouter.delete("/:id", (req, res) => {            // DELETE LIBRO
    
    const id = req.params.id;
    console.log(`DELETE /api/v2/libri/${req.params.id}`);

    db.run(DELETE_LIBRO, [id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes === 0) {
            res.status (404).json({ message: "Libro non presente in database" });
        } else {
            res.json({ message: "Libro cancellato con successo"});
        }
    });
});




function validaLibro(libro) {                   // validazione del body
    let errorMessage;

    if (!libro) {
        errorMessage = "Libro non presente";
    }
    if (isNaN(libro.numero_pagine)) {
        errorMessage = "Il numero di pagine deve essere un valore numerico intero";
    }
    return errorMessage;
}

export default libriRouter;