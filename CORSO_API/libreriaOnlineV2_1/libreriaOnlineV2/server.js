import express from 'express';
import bodyParser from 'body-parser';
import sqlite3 from 'sqlite3';
import swaggerUi from 'swagger-ui-express';
import swaggerDocument from './doc/swagger.json' with { type: 'json' };
import { CREATE_LIBRI_TABLE } from './database/script_libri.js';
import libriRouter from './routes/libriRouter.js';


const app = express();
app.use(bodyParser.json());

const PORT = 3000;
const BASE_PATH = "/api/v2";
export const db = new sqlite3.Database("./database/libreria.db");


// Inizializzazione rotte
app.use(`${BASE_PATH}/libri`, libriRouter);


// attivo il listener dell'applicazione sulla porta 3000
app.listen(PORT, () => {
    console.log(`Server attivo sulla porta ${PORT}`);
    initializeDatabase();
});


// endpoint di prova
app.get("/", (req, res) => {
    res.send("Benvenuto nella tua libreria online!");
});


/* UTILITIES */
function initializeDatabase() {
    console.log("Inizializzazione database...");

    db.exec(CREATE_LIBRI_TABLE, (err) => {
        if (err) {
            console.error("Errore durante la creazione della tabella libri: ", err);
        } else {
            console.log("Tabella libri inizializzata correttamente");
        }
    });
}