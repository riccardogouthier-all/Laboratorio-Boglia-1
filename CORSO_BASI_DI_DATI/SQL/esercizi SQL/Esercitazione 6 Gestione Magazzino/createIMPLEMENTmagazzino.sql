-- Creazione Tabella Categorie
CREATE TABLE Categorie (
    id_categoria INT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descrizione TEXT
);

-- Creazione Tabella Fornitori
CREATE TABLE Fornitori (
    id_fornitore INT PRIMARY KEY,
    ragione_sociale VARCHAR(100) NOT NULL,
    citta VARCHAR(50),
    email VARCHAR(100) CHECK (email LIKE '%@%')
);

-- Creazione Tabella Prodotti
CREATE TABLE Prodotti (
    id_prodotto INT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    prezzo_unitario DECIMAL(10, 2) NOT NULL CHECK (prezzo_unitario > 0),
    quantita_stock INT DEFAULT 0 CHECK (quantita_stock >= 0),
    id_categoria INT,
    id_fornitore INT,
    FOREIGN KEY (id_categoria) REFERENCES Categorie(id_categoria) ON DELETE SET NULL,
    FOREIGN KEY (id_fornitore) REFERENCES Fornitori(id_fornitore) ON DELETE CASCADE
);



INSERT INTO Categorie VALUES (1, 'Elettronica', 'Dispositivi hardware e gadget');
INSERT INTO Categorie VALUES (2, 'Arredamento', 'Mobili e ufficio');

INSERT INTO Fornitori VALUES (10, 'TechSpA', 'Milano', 'info@techspa.it');
INSERT INTO Fornitori VALUES (20, 'WoodDesign', 'Torino', 'sales@wood.com');

INSERT INTO Prodotti VALUES (101, 'Laptop Pro', 1200.00, 15, 1, 10);
INSERT INTO Prodotti VALUES (102, 'Mouse Wireless', 25.50, 50, 1, 10);
INSERT INTO Prodotti VALUES (103, 'Scrivania Legno', 150.00, 5, 2, 20);
INSERT INTO Prodotti VALUES (104, 'Sedia Ergonomica', 89.99, 0, 2, 20);
INSERT INTO Prodotti VALUES (105, 'Monitor 4K', 350.00, 8, 1, 10);

INSERT INTO Categorie (id_categoria, nome, descrizione) VALUES 
(3, 'Periferiche', 'Accessori per computer e input/output'),
(4, 'Illuminazione', 'Lampade e sistemi di luce per ufficio'),
(5, 'Cancelleria', 'Materiale di consumo per ufficio');

INSERT INTO Fornitori (id_fornitore, ragione_sociale, citta, email) VALUES 
(30, 'OfficeSupply Co.', 'Bologna', 'ordini@officesupply.it'),
(40, 'LuceDesign', 'Firenze', 'contact@lucedesign.com'),
(50, 'Global Logistics', 'Milano', 'logistics@global.com'),
(60, 'Cartiera Veneta', 'Padova', 'info@cartieraveneta.it');

INSERT INTO Prodotti (id_prodotto, nome, prezzo_unitario, quantita_stock, id_categoria, id_fornitore) VALUES 
-- Elettronica & Periferiche (TechSpA)
(106, 'Tastiera Meccanica', 75.00, 25, 3, 10),
(107, 'Cuffie Noise Cancelling', 199.00, 12, 1, 10),
(108, 'Webcam HD', 45.90, 0, 3, 10),

-- Arredamento & Illuminazione (WoodDesign e LuceDesign)
(109, 'Libreria Modulare', 210.00, 3, 2, 20),
(110, 'Lampada da Scrivania LED', 35.00, 40, 4, 40),
(111, 'Piantana Alogena', 120.00, 7, 4, 40),

-- Cancelleria (OfficeSupply e Cartiera Veneta)
(112, 'Risme Carta A4 (5pz)', 22.50, 100, 5, 60),
(113, 'Set Penne Gel', 12.00, 200, 5, 30),
(114, 'Organizer da tavolo', 18.50, 15, 5, 30),

-- Altri prodotti misti
(115, 'Hard Disk Esterno 2TB', 85.00, 30, 1, 50),
(116, 'Smartphone Entry Level', 150.00, 10, 1, 50),
(117, 'Cavo HDMI 2m', 9.99, 150, 3, 50);
