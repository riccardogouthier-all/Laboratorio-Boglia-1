export const CREATE_CLIENTI_TABLE = `CREATE TABLE IF NOT EXISTS clienti (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        nome TEXT NOT NULL,
                                        cognome TEXT NOT NULL,
                                        email TEXT NOT NULL,
                                        telefono TEXT
                                    )`;

export const SELECT_ALL_CLIENTI = "SELECT * FROM clienti";

export const SELECT_CLIENTE_BY_ID = "SELECT * FROM clienti WHERE id = ?";

export const INSERT_CLIENTE = "INSERT INTO clienti (nome, cognome, email, telefono) VALUES (?, ?, ?, ?)";

export const UPDATE_CLIENTE = "UPDATE clienti SET nome = ?, cognome = ?, email = ?, telefono = ? WHERE id = ?";

export const DELETE_CLIENTE = "DELETE FROM clienti WHERE id = ?";