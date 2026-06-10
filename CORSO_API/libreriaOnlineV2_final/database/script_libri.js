export const CREATE_LIBRI_TABLE = `CREATE TABLE IF NOT EXISTS libri (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        titolo TEXT NOT NULL,
                                        autore TEXT NOT NULL,
                                        editore TEXT NOT NULL,
                                        genere TEXT,
                                        numero_pagine INTEGER
                                    )`;

export const SELECT_ALL = "SELECT * FROM libri";

export const SELECT_BY_ID = "SELECT * FROM libri WHERE id = ?";

export const SELECT_BY_TITOLO = "SELECT * FROM libri WHERE LOWER(titolo) LIKE '%' || LOWER(?) || '%'";

export const INSERT_LIBRO = "INSERT INTO libri (titolo, autore, editore, genere, numero_pagine) VALUES (?, ?, ?, ?, ?)";

export const UPDATE_LIBRO = "UPDATE libri SET titolo = ?, autore = ?, editore = ?, genere = ?, numero_pagine = ? WHERE id = ?";

export const DELETE_LIBRO = "DELETE FROM libri WHERE id = ?";