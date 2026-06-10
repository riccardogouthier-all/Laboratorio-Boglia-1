// Tabella principale delle playlist
export const CREATE_PLAYLIST_TABLE = `
CREATE TABLE IF NOT EXISTS playlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    descrizione TEXT
)
`;

// Tabella di giunzione playlist ↔ canzoni (molti-a-molti)
export const CREATE_PLAYLIST_CANZONI_TABLE = `
CREATE TABLE IF NOT EXISTS playlist_canzoni (
    playlist_id INTEGER NOT NULL,
    canzone_id  INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, canzone_id),
    FOREIGN KEY (playlist_id) REFERENCES playlist(id)  ON DELETE CASCADE,
    FOREIGN KEY (canzone_id)  REFERENCES canzoni(id)   ON DELETE CASCADE
)
`;

export const SELECT_ALL_PLAYLIST    = "SELECT * FROM playlist";
export const SELECT_PLAYLIST_BY_ID  = "SELECT * FROM playlist WHERE id = ?";
export const INSERT_PLAYLIST        = "INSERT INTO playlist (nome, descrizione) VALUES (?, ?)";
export const UPDATE_PLAYLIST        = "UPDATE playlist SET nome = ?, descrizione = ? WHERE id = ?";
export const PATCH_PLAYLIST_NOME    = "UPDATE playlist SET nome = ? WHERE id = ?";
export const PATCH_PLAYLIST_DESC    = "UPDATE playlist SET descrizione = ? WHERE id = ?";
export const DELETE_PLAYLIST        = "DELETE FROM playlist WHERE id = ?";

// Query per le canzoni di una playlist
export const SELECT_CANZONI_BY_PLAYLIST = `
SELECT c.*
FROM   canzoni c
JOIN   playlist_canzoni pc ON c.id = pc.canzone_id
WHERE  pc.playlist_id = ?
`;
export const INSERT_CANZONE_IN_PLAYLIST = `INSERT OR IGNORE INTO playlist_canzoni (playlist_id, canzone_id) VALUES (?, ?)
`;
export const DELETE_CANZONE_FROM_PLAYLIST = `DELETE FROM playlist_canzoni WHERE playlist_id = ? AND canzone_id = ?
`;