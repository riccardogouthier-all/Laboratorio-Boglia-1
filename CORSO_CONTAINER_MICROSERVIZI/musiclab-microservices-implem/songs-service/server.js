import express from 'express';
import cors from 'cors';
import sqlite3 from 'sqlite3';
import swaggerUi from 'swagger-ui-express';
import { fileURLToPath } from 'url';
import path from 'path';
import { readFileSync } from 'fs';
import { CREATE_CANZONI_TABLE } from './db/schema.js';
import canzoniRouter from './routes/canzoniRouter.js';
import { connectPublisher } from './events/publisher.js';
import { seedIfEmpty } from './db/seed.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const swaggerDocument = JSON.parse(
  readFileSync(path.join(__dirname, 'doc/swagger.json'), 'utf-8')
);

const app  = express();
const PORT = process.env.PORT || 4001;
const DB_PATH = process.env.DB_PATH || '/app/data/songs.db';

app.use(express.json());
app.use(cors());

export const db = new sqlite3.Database(DB_PATH);

app.use('/api/canzoni', canzoniRouter);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'songs-service' }));

function createTable() {
  return new Promise((resolve, reject) => {
    db.run('PRAGMA journal_mode = WAL');
    db.exec(CREATE_CANZONI_TABLE, (err) => (err ? reject(err) : resolve()));
  });
}

app.listen(PORT, async () => {
  console.log(`songs-service in ascolto sulla porta ${PORT}`);
  try {
    await createTable();
    console.log('Tabella canzoni pronta');
    await connectPublisher();
    await seedIfEmpty(db);
  } catch (err) {
    console.error('Errore in fase di avvio:', err);
  }
});

