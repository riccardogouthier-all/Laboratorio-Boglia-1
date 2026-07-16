import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Cartella dove verranno collocati i file audio reali (una volta scaricati).
// Configurabile via variabile d'ambiente AUDIO_TRACKS_DIR, perché il percorso
// basato su __dirname punta dentro l'immagine Docker (non persistente, non
// accessibile dall'host) mentre qui serve un percorso montato come volume,
// come /app/data lo è per il database (vedi DB_PATH in docker-compose.yml).
const CARTELLA_TRACCE_AUDIO = process.env.AUDIO_TRACKS_DIR || path.join(__dirname, 'tracce audio');

/**
 * Caratteri non ammessi (o problematici) nei nomi file su Windows/Unix.
 * Sostituiti con "-" per evitare 404 o errori di filesystem.
 */
const CARATTERI_NON_VALIDI_NOME_FILE = /[/\\?%*:|"<>]/g;

/**
 * Sanifica un singolo campo (autore, album o titolo) prima di comporre
 * il nome file, rimuovendo caratteri non ammessi nei filesystem.
 * Gli spazi interni al campo vengono preservati così come sono nel CSV.
 *
 * @param {string} valore campo grezzo proveniente dal CSV
 * @returns {string} valore sanificato
 */
function sanificaCampoNomeFile(valore) {
  return String(valore ?? '').trim().replace(CARATTERI_NON_VALIDI_NOME_FILE, '-');
}

/**
 * Calcola il nome del file audio associato a un brano, in base ai suoi
 * metadati anziché all'id/posizione nel catalogo. Convenzione:
 * "{autore}_{album}_{titolo}.mp3".
 *
 * @param {string} artista
 * @param {string} album
 * @param {string} titolo
 * @returns {string} nome file audio (può non esistere ancora)
 */
function percorsoTracciaAudio(artista, album, titolo) {
  // Solo il nome del file: il path assoluto viene ricostruito da chi legge
  // il DB (es. canzoniRouter.js) unendo la propria cartella AUDIO_TRACKS_DIR
  // con questo nome. Salvare qui un path assoluto causerebbe un doppio
  // concatenamento (path.join non "resetta" su un path assoluto) e quindi 404.
  const a = sanificaCampoNomeFile(artista);
  const al = sanificaCampoNomeFile(album);
  const t = sanificaCampoNomeFile(titolo);
  return `${a}_${al}_${t}.mp3`;
}

/**
 * Converte una durata in formato "m:ss" (es. "3:45") in secondi totali.
 * @param {string} durataMMSS
 * @returns {number} durata in secondi
 */
function durataInSecondi(durataMMSS) {
  const parti = durataMMSS.split(':').map(Number);
  const [minuti, secondi] = parti;
  return minuti * 60 + secondi;
}

/**
 * Parser CSV minimale (senza dipendenze esterne), conforme a RFC 4180:
 * gestisce campi tra virgolette che contengono virgole o virgolette escapate ("").
 * Adatto a file piccoli/medi come il catalogo di un seed.
 *
 * @param {string} contenuto testo grezzo del file CSV
 * @returns {Array<Object>} righe come oggetti { nomeColonna: valore }
 */
function parseCsv(contenuto) {
  const righe = [];
  let riga = [];
  let campo = '';
  let dentroVirgolette = false;
  let intestazioni = null;

  const chiudiCampo = () => {
    riga.push(campo);
    campo = '';
  };

  const chiudiRiga = () => {
    chiudiCampo();
    if (riga.some((c) => c !== '')) {
      if (!intestazioni) {
        intestazioni = riga;
      } else {
        const oggetto = {};
        intestazioni.forEach((chiave, indice) => {
          oggetto[chiave.trim()] = (riga[indice] ?? '').trim();
        });
        righe.push(oggetto);
      }
    }
    riga = [];
  };

  // normalizza fine riga e rimuove eventuale BOM iniziale
  const testo = contenuto.replace(/\r\n/g, '\n').replace(/^\uFEFF/, '');

  for (let i = 0; i < testo.length; i++) {
    const carattere = testo[i];

    if (dentroVirgolette) {
      if (carattere === '"') {
        if (testo[i + 1] === '"') {
          campo += '"';
          i++;
        } else {
          dentroVirgolette = false;
        }
      } else {
        campo += carattere;
      }
      continue;
    }

    if (carattere === '"') {
      dentroVirgolette = true;
    } else if (carattere === ',') {
      chiudiCampo();
    } else if (carattere === '\n') {
      chiudiRiga();
    } else {
      campo += carattere;
    }
  }
  if (campo !== '' || riga.length > 0) {
    chiudiRiga();
  }

  return righe;
}

/**
 * Legge il catalogo brani da un file CSV con colonne
 * Titolo, Artista, Album, Genere, Anno, Durata (formato mm:ss),
 * e restituisce l'elenco pronto per l'inserimento in DB,
 * completo del nome del file audio corrispondente, calcolato da
 * Artista/Album/Titolo (non più dall'id/posizione nel CSV).
 *
 * @param {string} percorsoCsv percorso al file CSV del catalogo
 * @returns {Array<{titolo:string, artista:string, album:string, genere:string, anno:number, durata_secondi:number, file_audio:string}>}
 */
export function caricaCatalogoDaCsv(percorsoCsv) {
  const contenuto = fs.readFileSync(percorsoCsv, 'utf-8');
  const righe = parseCsv(contenuto);

  return righe.map((r) => {
    return {
      titolo: r.Titolo,
      artista: r.Artista,
      album: r.Album,
      genere: r.Genere,
      anno: parseInt(r.Anno, 10),
      durata_secondi: durataInSecondi(r.Durata),
      file_audio: percorsoTracciaAudio(r.Artista, r.Album, r.Titolo),
    };
  });
}

export { percorsoTracciaAudio, CARTELLA_TRACCE_AUDIO };