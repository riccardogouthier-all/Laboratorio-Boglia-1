import express from 'express';
import { db } from '../server.js';
import {SELECT_ALL, SELECT_BY_ID, SELECT_BY_TITOLO,
        INSERT_LIBRO, UPDATE_LIBRO, DELETE_LIBRO} from '../database/script_libri.js';


const libriRouter = express.Router();


libriRouter.get("/", (req, res) => {
    console.log("GET /api/v2/libri")

    db.all(SELECT_ALL, (err, rows) => {
        if (err) {
            res.status(500).json({ error: message });
        } else {
            res.json(rows);
        }
    });
});


libriRouter.post("/", (req, res) => {
    console.log("POST /api/v2/libri")

    // controllo che il body esista
    if (!req.body) {
        res.status(400).json({ error: "Libro non presente"});
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

export default libriRouter;