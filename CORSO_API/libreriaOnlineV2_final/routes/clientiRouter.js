import express from 'express';
import { db } from "../server.js";
import { SELECT_ALL_CLIENTI, SELECT_CLIENTE_BY_ID, INSERT_CLIENTE,
    UPDATE_CLIENTE, DELETE_CLIENTE } from "../database/script_clienti.js";


const clientiRouter = express.Router();

clientiRouter.get("/", (req, res) => {
    console.log("GET /api/v2/clienti");

    db.all(SELECT_ALL_CLIENTI, (err, rows) => {
        if (err) {
            res.status(500).json({ error: err.message });
        } else {
            res.json(rows);
        }
    });
});

clientiRouter.get("/:id", (req, res) => {
    console.log(`GET /api/v2/clienti/${req.params.id}`);

    db.get(SELECT_CLIENTE_BY_ID, [req.params.id], function(err, row) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (!row) {
            res.status(404).json({ message: "Cliente non trovato con l'id specificato" });
        } else {
            res.json(row);
        }
    });
});


clientiRouter.post("/", (req, res) => {
    console.log("POST /api/v2/clienti");

    const errorMessage = validaCliente(req.body);
    if (errorMessage) {
        res.status(400).json({ error: errorMessage });
        return;
    }

    // estraggo le proprietà dal body
    const { nome, cognome, email, telefono } = req.body;

    db.run(INSERT_CLIENTE, [nome, cognome, email, telefono], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        } else {
            res.status(201).json({ message: `Cliente creato con ID ${this.lastID}` });
        }
    });
});

clientiRouter.put("/:id", (req, res) => {
    const id = req.params.id;
    console.log(`PUT /api/v2/clienti/${id}`);
    const { nome, cognome, email, telefono } = req.body;

    db.run(UPDATE_CLIENTE, [nome, cognome, email, telefono, id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes === 0) {
            res.status(404).json({ message: "Cliente non presente in database" });
        } else {
            res.json({ message: "Cliente aggiornato con successo" });
        }
    });
});

clientiRouter.delete("/:id", (req, res) => {
    const id = req.params.id;
    console.log(`DELETE /api/v2/clienti/${id}`);

    db.run(DELETE_CLIENTE, [id], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
        } else if (this.changes === 0) {
            res.status(404).json({ message: "Cliente non presente in database" });
        } else {
            res.json({ message: "Cliente eliminato con successo" });
        }
    });
});


/* UTILITY */
function validaCliente(cliente) {
    let errorMessage;

    if (!cliente) {
        errorMessage = "Cliente non presente.";
    }
    if (cliente.email && !cliente.email.includes("@")) {
        errorMessage = "L'email non è valida.";
    }

    return errorMessage;
}


export default clientiRouter;