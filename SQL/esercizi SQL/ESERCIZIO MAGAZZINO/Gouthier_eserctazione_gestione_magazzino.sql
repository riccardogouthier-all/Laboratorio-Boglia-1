-- 3. Esercitazione: 30 Query SQL
-- Ecco una lista di query divise per livello di difficoltà crescente.

-- Query di Base (Selezione e Filtro)
-- Selezionare tutti i prodotti.
select * from prodotti;
-- Selezionare nome e prezzo dei prodotti con prezzo superiore a 100€.
select nome, prezzo_unitario from prodotti where prezzo_unitario>100;
-- Elencare i fornitori di Milano.
select * from fornitori where citta = "Milano";
-- Trovare i prodotti con quantità in stock pari a 0 (esauriti).
select * from prodotti where quantita_stock = 0;
-- Selezionare i prodotti che contengono la parola 'Laptop' nel nome.
select * from prodotti where nome like '%laptop%';
-- Elencare le categorie in ordine alfabetico.
select * from categorie order by nome;
-- Trovare i prodotti con prezzo compreso tra 50€ e 500€.
select * from prodotti where prezzo_unitario between 50 and 500;
-- Mostrare i fornitori che non hanno un'email specificata (se fosse NULL).
select * from fornitori where email is null;
-- Selezionare i primi 3 prodotti più costosi.
select * from prodotti order by prezzo_unitario desc limit 3;
-- Calcolare il valore totale della merce (prezzo * quantità) per ogni prodotto.
select (prezzo_unitario * quantita_stock) as 'Valore prodotti' from prodotti;





-- Query con Join (Relazioni tra tabelle)
-- Visualizzare nome prodotto e nome della relativa categoria.
select id_prodotto, categorie.id_categoria from prodotti join categorie on prodotti.id_categoria = categorie.id_categoria;
-- Elencare i prodotti insieme alla ragione sociale del loro fornitore.
select prodotti.nome as nome_prodotto, fornitori.ragione_sociale as ragione_sociale_fornitore from prodotti join fornitori on prodotti.id_fornitore = fornitori.id_fornitore;
-- Trovare tutti i prodotti della categoria 'Elettronica'.
select prodotti.nome as nome_prodotto from prodotti join categorie on prodotti.id_categoria = categorie.id_categoria where categorie.nome = 'Elettronica';
-- Mostrare i prodotti forniti da 'TechSpA'.
select prodotti.nome as nome_prodotto from prodotti join fornitori on prodotti.id_fornitore = fornitori.id_fornitore where fornitori.ragione_sociale = 'TechSpA';
-- Elencare i nomi dei prodotti e le città dei loro fornitori.
select prodotti.nome, fornitori.citta as citta_fornitore from prodotti join fornitori on prodotti.id_fornitore = fornitori.id_fornitore;
-- Visualizzare i prodotti della categoria 'Arredamento' con stock > 0.
select prodotti.nome as nome_prodotto from prodotti join categorie on prodotti.id_categoria = categorie.id_categoria where categorie.nome = 'Arredamento' and quantita_stock > 0;
-- Mostrare le categorie che hanno almeno un prodotto fornito da un fornitore di 'Torino'.
select distinct categorie.nome from prodotti join categorie using(id_categoria) join fornitori using(id_fornitore) where fornitori.citta = 'Torino';
-- Visualizzare i prodotti (nome) e il fornitore, ma solo se il prezzo è > 200€.
select nome, fornitori.ragione_sociale from prodotti join fornitori on prodotti.id_fornitore = fornitori.id_fornitore where prezzo_unitario > 200;
-- Lista completa: Nome Prodotto, Categoria, Fornitore.
select prodotti.nome, categorie.nome, fornitori.ragione_sociale from prodotti join categorie using(id_categoria) join fornitori using(id_fornitore);
-- Trovare i nomi dei fornitori che forniscono prodotti nella categoria 'Elettronica'.
select distinct fornitori.ragione_sociale from fornitori join prodotti on fornitori.id_fornitore = prodotti.id_fornitore join categorie on prodotti.id_categoria = categorie.id_categoria where categorie.nome = 'Elettronica';





-- Query di Aggregazione e Funzioni (Statistiche)
-- Contare quanti prodotti ci sono in totale nel database.
select count(*) as numero_oggetti from prodotti;
-- Calcolare il prezzo medio dei prodotti.
select avg(prezzo_unitario) as prezzo_medio from prodotti;

-- Calcolare la somma totale degli articoli in magazzino.
select sum(quantita_stock) as tutto_magazzino from prodotti;
-- Trovare il prezzo massimo per ogni categoria.
select categorie.nome, max(prezzo_unitario) from prodotti join categorie using(id_categoria) group by categorie.nome;

-- 25 Contare quanti prodotti fornisce ogni fornitore.
select fornitori.ragione_sociale, count(prodotti.id_prodotto) as numero_prodotti 
from fornitori 
join prodotti using(id_fornitore) 
group by fornitori.ragione_sociale;

-- Calcolare il valore totale economico del magazzino intero.
select sum(prezzo_unitario * quantita_stock) as valore_magazzino from prodotti;

-- 27 Mostrare le categorie che hanno più di 2 prodotti.
select categorie.nome, count(prodotti.id_prodotto) 
from categorie 
join prodotti using(id_categoria) 
group by categorie.nome 
having count(prodotti.id_prodotto) >2;

-- Trovare il fornitore che ha il prodotto più economico.
select fornitori.ragione_sociale, prodotti.nome, prodotti.prezzo_unitario from fornitori join prodotti on fornitori.id_fornitore = prodotti.id_fornitore where prodotti.prezzo_unitario = (select min(prezzo_unitario) from prodotti);
-- Calcolare la media dei prezzi dei prodotti per il fornitore 'TechSpA'.

-- Visualizzare le categorie e il numero di pezzi totali (somma stock) per ognuna.




-- Esempio di risoluzione (Query 25 & 27)
-- Se vuoi testare la logica più complessa:
-- -- Query 25: Numero prodotti per fornitore
-- SELECT F.ragione_sociale, COUNT(P.id_prodotto) AS Totale_Prodotti FROM Fornitori F LEFT JOIN Prodotti P ON F.id_fornitore = P.id_fornitore GROUP BY F.ragione_sociale;
-- -- Query 27: Categorie con più di 2 prodotti
-- SELECT C.nome, COUNT(P.id_prodotto) FROM Categorie C JOIN Prodotti P ON C.id_categoria = P.id_categoria GROUP BY C.nome HAVING COUNT(P.id_prodotto) > 2;