-- Esercitazione 7 - Daily routine
-- 1. Creazione Database e Utente
create database EsercizioSQL;
create user 'esercizio_user'@'localhost' identified by 'password123';
grant all privileges on EsercizioSQL.* to 'esercizio_user'@'localhost';
flush privileges;

-- Verifica
show grants for 'esercizio_user'@'localhost';

-- 2. Creazione Tabelle
use EsercizioSQL;
drop table if exists eserciziosql.clienti, eserciziosql.ordini, eserciziosql.prodotti;
CREATE TABLE Clienti (
id_cliente INT PRIMARY KEY AUTO_INCREMENT,
nome VARCHAR(50) NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE Prodotti (
id_prodotto INT PRIMARY KEY AUTO_INCREMENT,
nome VARCHAR(50) NOT NULL,
prezzo DECIMAL(10,2) CHECK (prezzo > 0)
);
CREATE TABLE Ordini (
id_ordine INT PRIMARY KEY AUTO_INCREMENT,
id_cliente INT,
id_prodotto INT,
quantita INT NOT NULL CHECK (quantita > 0),
data_ordine DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (id_cliente) REFERENCES Clienti(id_cliente) ON DELETE CASCADE,
FOREIGN KEY (id_prodotto) REFERENCES Prodotti(id_prodotto) ON DELETE CASCADE
);

-- Verifica
show tables;
describe clienti;
describe prodotti;
describe ordini;

-- 3. Inserimento Dati
INSERT INTO Clienti (nome, email) VALUES 
('Mario Rossi', 'mario@email.com'),
('Anna Verdi', 'anna@email.com');
INSERT INTO Prodotti (nome, prezzo) VALUES 
('Laptop', 1200.00),
('Mouse', 25.50);
INSERT INTO Ordini (id_cliente, id_prodotto, quantita) VALUES 
(1, 1, 1),
(2, 2, 2),
(1, 2, 1);

-- Verifica
SELECT * FROM Clienti; SELECT * FROM Ordini; SELECT * FROM prodotti;

-- 4. Query di Lettura
-- Ordini con tutti i dettagli
select o.*, c.nome, p.nome, p.prezzo + o.quantita as totale from ordini o
join clienti c using(id_cliente)
join prodotti p using(id_prodotto);
-- Ordini x cliente
select c.nome, count(o.id_ordine) as num_ordini from clienti c
join ordini o using(id_cliente)
group by c.id_cliente;
-- Clienti con >1 ordini
select c.nome, count(o.id_ordine) as num_ordini from clienti c
join ordini o using(id_cliente)
group by c.id_cliente having num_ordini > 1;
-- Totale speso per cliente
select c.nome, sum(p.prezzo * o.quantita) as totale_cliente
from clienti c
join ordini o using(id_cliente)
join prodotti p using(id_prodotto)
group by c.id_cliente
;

-- 5. Update e Delete
update prodotti set prezzo = 1300.00 where nome = 'Laptop';
update prodotti set prezzo = 1300.00 where id_prodotto = 1;		-- Giusta

delete from clienti where nome= 'Mario Rossi';
delete from ordini where id_ordine = 1;		-- Giusta

-- Verifica
select * from ordini;

-- 6. Test Vincoli
insert into ordini (id_cliente,id_prodotto,quantita) values(1,1,-1);
-- Fallisce perché il numero quantita è negativo 

-- 7. Eliminazione Finale
use eserciziosql;
delete from ordini;
drop user 'esercizio_user'@'localhost';
drop database eserciziosql;

-- Verifica
show databases;