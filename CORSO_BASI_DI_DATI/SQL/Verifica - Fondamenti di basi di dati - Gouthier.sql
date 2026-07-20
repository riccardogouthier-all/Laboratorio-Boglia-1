# Riccardo Gouthier
# 2026-05-15
# Corso AWS Cloud Architecht 2026 - ACA 2026

-- Creazione database - PARTE A
CREATE DATABASE ai_lab_Riccardo_Gouthier;
USE ai_lab_Riccardo_Gouthier;

-- Creazione tabelle - PARTE A
CREATE TABLE Utente_Gouthier (
    idUtente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    dataNascita DATE NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    ruolo VARCHAR(50) NOT NULL,
    dataRegistrazione DATE NOT NULL
);

CREATE TABLE Dataset_Gouthier (
    idDataset INT AUTO_INCREMENT PRIMARY KEY,
    nomeDataset VARCHAR(200) NOT NULL,
    descrizione TEXT,
    lingua VARCHAR(50) NOT NULL,
    dataCreazione DATE NOT NULL,
    idCreatore INT NOT NULL,
    licenza VARCHAR(100) NOT NULL,
    CONSTRAINT uq_nomeDataset UNIQUE (nomeDataset),					-- aggiunta unique
    CONSTRAINT fk_dataset_creatore
        FOREIGN KEY (idCreatore)
        REFERENCES Utente_Gouthier(idUtente)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE Documento_Gouthier (
    idDocumento INT AUTO_INCREMENT PRIMARY KEY,
    titolo VARCHAR(300) NOT NULL,
    testo TEXT,
    dataInserimento DATE NOT NULL,
    idDataset INT NOT NULL,
    lunghezzaCaratteri INT NOT NULL,
    CONSTRAINT fk_documento_dataset
        FOREIGN KEY (idDataset)
        REFERENCES Dataset_Gouthier(idDataset)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_documento_idDataset (idDataset)					-- aggiunta index
);

CREATE TABLE Annotazione_Gouthier (
    idAnnotazione INT AUTO_INCREMENT PRIMARY KEY,
    idDocumento INT NOT NULL,
    idUtente INT NOT NULL,
    etichetta VARCHAR(50) NOT NULL,
    confidenza DECIMAL(3,2) NOT NULL,
    dataAnnotazione DATE NOT NULL,
    CONSTRAINT fk_annotazione_documento
        FOREIGN KEY (idDocumento)
        REFERENCES Documento_Gouthier(idDocumento)
        ON DELETE CASCADE,
    CONSTRAINT fk_annotazione_utente
        FOREIGN KEY (idUtente)
        REFERENCES Utente_Gouthier(idUtente)
        ON DELETE RESTRICT,
    INDEX idx_annotazione_doc_utente (idDocumento, idUtente)					-- aggiunta index
);

-- Riempimento tabelle - PARTE B
INSERT INTO Utente_Gouthier (nome, cognome, dataNascita, email, ruolo, dataRegistrazione) VALUES
('Riccardo', 'Gouthier', '2003-01-24', 'riccardo.gouthier@example.com', 'ricercatore', '2026-05-01'),
('Laura', 'Bianchi', '2002-09-15', 'laura.bianchi@example.com', 'annotatore', '2026-05-02'),
('Marco', 'Rossi', '2001-11-30', 'marco.rossi@example.com', 'admin', '2026-05-03');

INSERT INTO Dataset_Gouthier (nomeDataset, descrizione, lingua, dataCreazione, idCreatore, licenza) VALUES
('Dataset_A', 'Collezione di testi per analisi AI', 'italiano', '2026-05-04', 1, 'CC BY 4.0'),
('Dataset_B', 'Dataset multilingua per classificazione', 'inglese', '2026-05-05', 2, 'MIT');

INSERT INTO Documento_Gouthier (titolo, testo, dataInserimento, idDataset, lunghezzaCaratteri) VALUES
('Documento_1', 'Testo del documento 1.', '2026-05-06', 1, 23),
('Documento_2', 'Testo del documento 2.', '2026-05-06', 1, 23),
('Documento_3', 'Testo del documento 3.', '2026-05-07', 1, 23),
('Documento_4', 'Testo del documento 4.', '2026-05-07', 2, 23),
('Documento_5', 'Testo del documento 5.', '2026-05-08', 2, 23),
('Documento_6', 'Testo del documento 6.', '2026-05-08', 2, 23);

INSERT INTO Annotazione_Gouthier (idDocumento, idUtente, etichetta, confidenza, dataAnnotazione) VALUES
(1, 2, 'positivo', 0.90, '2026-05-09'),
(2, 1, 'neutro', 0.75, '2026-05-09'),
(3, 3, 'negativo', 0.80, '2026-05-09'),
(4, 2, 'positivo', 0.95, '2026-05-10'),
(5, 1, 'spam', 0.60, '2026-05-10'),
(6, 2, 'neutro', 0.70, '2026-05-10'),
(1, 3, 'positivo', 0.85, '2026-05-11'),
(2, 2, 'negativo', 0.40, '2026-05-11'),
(4, 1, 'neutro', 0.78, '2026-05-11'),
(3, 3, 'positivo', 0.88, '2026-05-11');

-- Scrittura query - PARTE C
-- Q1
SELECT d.titolo, ds.nomeDataset, ds.lingua, u.nome, u.cognome
FROM Documento_Gouthier d
JOIN Dataset_Gouthier ds ON d.idDataset = ds.idDataset
JOIN Utente_Gouthier u ON ds.idCreatore = u.idUtente;
-- Output
/*
| titolo      | nomeDataset | lingua   | nome     | cognome  |
| ----------- | ----------- | -------- | -------- | -------- |
| Documento_1 | Dataset_A   | italiano | Riccardo | Gouthier |
| Documento_2 | Dataset_A   | italiano | Riccardo | Gouthier |
| Documento_3 | Dataset_A   | italiano | Riccardo | Gouthier |
| Documento_4 | Dataset_B   | inglese  | Laura    | Bianchi  |
| Documento_5 | Dataset_B   | inglese  | Laura    | Bianchi  |
| Documento_6 | Dataset_B   | inglese  | Laura    | Bianchi  |
*/

-- Q2
SELECT d.titolo, u.nome, u.cognome, a.confidenza
FROM Annotazione_Gouthier a
JOIN Documento_Gouthier d ON a.idDocumento = d.idDocumento
JOIN Utente_Gouthier u ON a.idUtente = u.idUtente
WHERE a.etichetta = 'positivo';
-- Output
/*
| titolo      | nome  | cognome | confidenza |
| ----------- | ----- | ------- | ---------- |
| Documento_1 | Laura | Bianchi | 0.90       |
| Documento_4 | Laura | Bianchi | 0.95       |
| Documento_1 | Marco | Rossi   | 0.85       |
| Documento_5 | Marco | Rossi   | 0.88       |
*/

-- Q3
SELECT ds.nomeDataset, COUNT(d.idDocumento) AS totaleDocumenti
FROM Dataset_Gouthier ds
LEFT JOIN Documento_Gouthier d ON ds.idDataset = d.idDataset
GROUP BY ds.idDataset, ds.nomeDataset;
-- Output
/*
| nomeDataset | totaleDocumenti |
| ----------- | --------------- |
| Dataset_A   | 3               |
| Dataset_B   | 3               |
*/

-- Q4
SELECT etichetta, AVG(confidenza) AS confidenzaMedia
FROM Annotazione_Gouthier
GROUP BY etichetta;
-- Output
/*
| etichetta | confidenzaMedia |
| --------- | --------------- |
| positivo  | 0.90            |
| neutro    | 0.74            |
| negativo  | 0.60            |
| spam      | 0.60            |
*/

-- Q5
SELECT nome, cognome, dataRegistrazione, YEAR(dataRegistrazione) AS annoRegistrazione
FROM Utente_Gouthier
WHERE dataRegistrazione > '2026-05-01';
-- Output
/*
| nome  | cognome | dataRegistrazione | annoRegistrazione |
| ----- | ------- | ----------------- | ----------------- |
| Laura | Bianchi | 2026-05-02        | 2026              |
| Marco | Rossi   | 2026-05-03        | 2026              |
*/

-- Q6
SELECT d.idDocumento, d.titolo
FROM Documento_Gouthier d
WHERE NOT EXISTS (
    SELECT 1
    FROM Annotazione_Gouthier a
    WHERE a.idDocumento = d.idDocumento
);
-- Output
/*
| idDocumento | titolo      |
| ----------- | ----------- |
|             |             |

Nessun risultato perché ho dato annotazioni a tutti i documenti
*/

-- Q7
SELECT u.nome, u.cognome, COUNT(a.idAnnotazione) AS totaleAnnotazioni
FROM Utente_Gouthier u
JOIN Annotazione_Gouthier a ON u.idUtente = a.idUtente
GROUP BY u.idUtente, u.nome, u.cognome
ORDER BY totaleAnnotazioni DESC
LIMIT 1;
-- Output
/*
| nome  | cognome | totaleAnnotazioni |
| ----- | ------- | ----------------- |
| Laura | Bianchi | 4                 |
*/

-- Q8
SELECT ds.nomeDataset, AVG(d.lunghezzaCaratteri) AS lunghezzaMediaCaratteri
FROM Dataset_Gouthier ds
JOIN Documento_Gouthier d ON ds.idDataset = d.idDataset
GROUP BY ds.idDataset, ds.nomeDataset
HAVING COUNT(d.idDocumento) >= 3;
-- Output
/*
| nomeDataset | lunghezzaMediaCaratteri |
| ----------- | ----------------------- |
| Dataset_A   | 23.00                   |
| Dataset_B   | 23.00                   |
*/

-- Q9 - Query inversa 1
-- Output di partenza
/*
| titolo      | etichetta | confidenza |
| ----------- | --------- | ---------- |
| Documento_1 | positivo  | 0.90       |
| Documento_2 | neutro    | 0.75       |
*/
SELECT d.titolo, a.etichetta, a.confidenza
FROM Annotazione_Gouthier a
JOIN Documento_Gouthier d ON a.idDocumento = d.idDocumento
WHERE d.titolo IN ('Documento_1', 'Documento_2')
  AND (
      (d.titolo = 'Documento_1' AND a.etichetta = 'positivo' AND a.confidenza = 0.90)
      OR
      (d.titolo = 'Documento_2' AND a.etichetta = 'neutro' AND a.confidenza = 0.75)
  );
-- Q10 - Query inversa 2
-- Output di partenza
/*
| nomeDataset | totaleAnnotazioni |
| ----------- | ----------------- |
| Dataset_A   | 6                 |
| Dataset_B   | 4                 |
*/
SELECT ds.nomeDataset, COUNT(a.idAnnotazione) AS totaleAnnotazioni
FROM Dataset_Gouthier ds
JOIN Documento_Gouthier d ON ds.idDataset = d.idDataset
JOIN Annotazione_Gouthier a ON d.idDocumento = a.idDocumento
GROUP BY ds.idDataset, ds.nomeDataset;

-- Risposte alle domande - PARTE D
/*
1. Differenza tra chiave primaria e chiave esterna:

La chiave primaria identifica in modo univoco ogni record di una tabella e non può essere né duplicata né nulla.
La chiave esterna collega una tabella a un’altra, facendo riferimento alla chiave primaria della tabella esterna.
La primaria serve a riconoscere un record, la esterna a creare relazioni tra tabelle.

2. A cosa serve un indice:

Un indice serve ad velocizzare le ricerche e le operazioni di join su una tabella.
È utile quando si fanno molte query di ricerca su colonne specifiche.
Può peggiorare le prestazioni negli inserimenti, aggiornamenti e cancellazioni, perché il database deve aggiornare anche l’indice.

3. Differenza tra WHERE e HAVING:

WHERE filtra le righe prima del raggruppamento.
HAVING filtra i gruppi dopo GROUP BY.
In pratica, WHERE lavora sui record singoli, HAVING sui risultati aggregati.

4. Cos’è una subquery correlata:

Una subquery correlata è una sottoquery che dipende dalla query esterna e viene valutata per ogni riga della query principale.
Esempio:
SELECT nome, cognome
FROM Utente_Gouthier u
WHERE EXISTS (SELECT 1 FROM Annotazione_Gouthier a WHERE a.idUtente = u.idUtente);
*/
