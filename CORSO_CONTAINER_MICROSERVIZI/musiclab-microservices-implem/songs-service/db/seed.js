import path from 'path';
import { fileURLToPath } from 'url';
import { SELECT_ALL, INSERT_CANZONE } from './schema.js';
import { caricaCatalogoDaCsv } from './csvCatalog.js';
import { publishEvent } from '../events/publisher.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// File CSV con il catalogo reale, posto nella stessa cartella di questo file.
const PERCORSO_CSV_CATALOGO = path.join(__dirname, 'catalogo.csv');

/**
 * Se la tabella "canzoni" è vuota, la popola leggendo il catalogo da un file CSV
 * (catalogo.csv, nella stessa cartella di questo file) e pubblica un evento
 * "song.created" per ciascun brano, così che playlist-service sincronizzi
 * subito la propria cache locale.
 * Se la tabella contiene già dati (riavvio, volume persistente) non fa nulla.
 *
 * Nota: il campo file_audio calcolato in csvCatalog.js è ora derivato da
 * Artista/Album/Titolo (nome file "{autore}_{album}_{titolo}.mp3"), non
 * dall'id/posizione nel CSV: nessuna assunzione su ordine o id necessaria.
 */
export function seedIfEmpty(db) {
  return new Promise((resolve, reject) => {
    db.get('SELECT COUNT(*) AS totale FROM canzoni', (err, row) => {
      if (err) return reject(err);

      if (row.totale > 0) {
        console.log(`[seed] catalogo già popolato (${row.totale} brani), seeding saltato`);
        return resolve();
      }

      let canzoni;
      try {
        canzoni = caricaCatalogoDaCsv(PERCORSO_CSV_CATALOGO);
      } catch (errLettura) {
        return reject(errLettura);
      }

      console.log(`[seed] popolamento catalogo da CSV con ${canzoni.length} brani...`);

      db.serialize(() => {
        db.run('BEGIN TRANSACTION');
        const stmt = db.prepare(INSERT_CANZONE);
        for (const c of canzoni) {
          stmt.run([c.titolo, c.artista, c.album, c.genere, c.anno, c.durata_secondi, c.file_audio]);
        }
        stmt.finalize((errFinalize) => {
          if (errFinalize) {
            db.run('ROLLBACK');
            return reject(errFinalize);
          }
          db.run('COMMIT', (errCommit) => {
            if (errCommit) return reject(errCommit);
            console.log('[seed] catalogo inserito con successo');

            // rilegge le righe (con gli id assegnati da SQLite) e pubblica
            // un evento per ciascuna, per sincronizzare playlist-service
            db.all(SELECT_ALL, (errSelect, rows) => {
              if (errSelect) return reject(errSelect);
              rows.forEach((r) => publishEvent('song.created', r));
              console.log(`[seed] pubblicati ${rows.length} eventi song.created`);
              resolve();
            });
          });
        });
      });
    });
  });
}