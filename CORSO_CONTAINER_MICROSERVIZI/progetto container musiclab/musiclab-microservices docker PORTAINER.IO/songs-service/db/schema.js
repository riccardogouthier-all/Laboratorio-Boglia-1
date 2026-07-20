export const CREATE_CANZONI_TABLE = `
CREATE TABLE IF NOT EXISTS canzoni (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    titolo         TEXT    NOT NULL,
    artista        TEXT    NOT NULL,
    album          TEXT,
    genere         TEXT,
    anno           INTEGER,
    durata_secondi INTEGER
)
`;

export const SELECT_ALL        = "SELECT * FROM canzoni";
export const SELECT_BY_ID      = "SELECT * FROM canzoni WHERE id = ?";
export const SELECT_BY_TITOLO  = "SELECT * FROM canzoni WHERE LOWER(titolo)  LIKE '%' || LOWER(?) || '%'";
export const SELECT_BY_FILTERS = `SELECT * FROM canzoni
WHERE  (:titolo  IS NULL OR LOWER(titolo)  LIKE '%' || LOWER(:titolo)  || '%')
AND    (:artista IS NULL OR LOWER(artista) LIKE '%' || LOWER(:artista) || '%')
`;

export const INSERT_CANZONE = `
INSERT INTO canzoni (titolo, artista, album, genere, anno, durata_secondi)
VALUES (?, ?, ?, ?, ?, ?)
`;
export const UPDATE_CANZONE = `
UPDATE canzoni
SET    titolo = ?, artista = ?, album = ?, genere = ?, anno = ?, durata_secondi = ?
WHERE  id = ?
`;
export const DELETE_CANZONE = "DELETE FROM canzoni WHERE id = ?";
