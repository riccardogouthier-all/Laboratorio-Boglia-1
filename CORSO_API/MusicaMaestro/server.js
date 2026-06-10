import express from 'express';
import bodyParser from 'body-parser';
import sqlite3 from 'sqlite3';
import swaggerUi from 'swagger-ui-express';
import swaggerDocument from './doc/swagger.json' with { type: 'json' };
import { CREATE_CANZONI_TABLE } from './database/script_canzoni.js';
import { CREATE_PLAYLIST_TABLE, CREATE_PLAYLIST_CANZONI_TABLE } from './database/script_playlist.js';
import canzoniRouter from './routes/canzoniRouter.js';
import playlistRouter from './routes/playlistRouter.js';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const app  = express();
const PORT = 3000;
const BASE_PATH = '/api';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

app.use(bodyParser.json());
app.use(cors());
app.use(express.static(__dirname));

export const db = new sqlite3.Database('./database/musica.db');

// Rotte
app.use(`${BASE_PATH}/canzoni`,  canzoniRouter);
app.use(`${BASE_PATH}/playlist`, playlistRouter);

// Swagger UI
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Listener
app.listen(PORT, () => {
console.log(`Server attivo sulla porta ${PORT}`);
initializeDatabase();
});

app.get('/', (req, res) => {
res.sendFile(path.join(__dirname, 'index.html'));
});

/* ── UTILITIES ─────────────────────────────── */
function initializeDatabase() {
console.log('Inizializzazione database...');

db.exec(CREATE_CANZONI_TABLE, (err) => {
    if (err) console.error('Errore tabella canzoni:', err);
    else     console.log('Tabella canzoni pronta');
});

  // PRAGMA per attivare i foreign key (necessario per ON DELETE CASCADE)
db.run('PRAGMA foreign_keys = ON');

db.exec(CREATE_PLAYLIST_TABLE, (err) => {
    if (err) console.error('Errore tabella playlist:', err);
    else {
        console.log('Tabella playlist pronta');
        db.exec(CREATE_PLAYLIST_CANZONI_TABLE, (err2) => {
            if (err2) console.error('Errore tabella playlist_canzoni:', err2);
            else      console.log('Tabella playlist_canzoni pronta');
            });
        }
    });
}