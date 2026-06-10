import express from 'express';
import bodyParser from 'body-parser';
import sqlite3 from 'sqlite3';
import swaggerUi from 'swagger-ui-express';
import swaggerDocument from './doc/swagger.json' with { type: 'json' };
import { CREATE_CANZONI_TABLE } from './database/script_canzoni.js';
import { CREATE_CLIENTI_TABLE } from './database/script_clienti.js';
import canzoniRouter from './routes/canzoniRouter.js';
import clientiRouter from './routes/clientiRouter.js';
import cors from 'cors';


const app = express();
const PORT = 3000;
const BASE_PATH = "/api/v2";
app.use(bodyParser.json());
app.use(cors());

export const db = new sqlite3.Database("./database/musica.db");

// Inizializzazione rotte
app.use(`${BASE_PATH}/canzoni`, canzoniRouter);
app.use(`${BASE_PATH}/clienti`, clientiRouter);

// Integrazione Swagger UI
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Listener
app.listen(PORT, () => {
    console.log(`Server attivo sulla porta ${PORT}`);
    initializeDatabase();
});

// Endpoint di prova
app.get("/", (req, res) => {
    res.send("Benvenuto nel tuo catalogo musicale!");
});


/* UTILITIES */
function initializeDatabase() {
    console.log("Inizializzazione database...");

    db.exec(CREATE_CANZONI_TABLE, (err) => {
        if (err) {
            console.error("Errore durante la creazione della tabella canzoni: ", err);
        } else {
            console.log("Tabella canzoni inizializzata correttamente");
        }
    });

    db.exec(CREATE_CLIENTI_TABLE, (err) => {
        if (err) {
            console.error("Errore durante la creazione della tabella clienti:", err.message);
        } else {
            console.log("Tabella clienti inizializzata correttamente.");
        }
    });
}
