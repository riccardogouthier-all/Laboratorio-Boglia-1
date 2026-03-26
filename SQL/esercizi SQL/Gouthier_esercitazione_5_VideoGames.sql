-- Esercizio 1
select * from games;
-- Esercizio 2
select game from games;
-- Esercizio 3
select * from games where year = '2020';
-- Esercizio 4
select * from games where genre = 'Action';
-- Esercizio 5
select * from games where publisher = 'Nintendo';
-- Esercizio 6
select * from games where genre = 'RPG' and publisher = 'Square Enix';
-- Esercizio 7
select * from games where original_platform = 'Playstation';
-- Esercizio 8
select * from games where year <= '2000';
-- Esercizio 9
select genre from games group by genre;
-- Esercizio 10
select * from games order by year desc;
-- Esercizio 11
select * from games where genre != 'Action' or 'adventure';
-- Esercizio 12
select * from games where year between '2000' and '2010';
-- Esercizio 13
select game, publisher from games where year >= '2015' order by publisher;
-- Esercizio 14
select count(*) from games;
-- Esercizio 15
select genre ,count(*) from games group by genre;
-- Esercizio 16
select * from games where year = (select max(year) from games); 
-- Esercizio 17
select publisher, count(*) from games group by publisher;
-- Esercizio 18
select genre, count(*) from games group by genre order by count(*) desc LIMIT 1;
-- Esercizio 19
select year, count(*) from games group by year order by year;
-- Esercizio 20
SELECT Game, original_platform, LENGTH(Original_platform) - LENGTH(REPLACE(Original_platform, ',', '')) + 1 AS numero_piattaforme FROM games having numero_piattaforme > 1 ORDER BY numero_piattaforme desc;
-- Esercizio 21
SELECT g1.Game, g1.year, g1.Publisher, g2.Publisher FROM games g1 JOIN games g2 ON g1.Game = g2.Game and g1.year = g2.year and g1.Publisher != g2.Publisher ORDER BY g1.Game;
-- Esercizio 22 
SELECT Publisher, COUNT(distinct Original_platform) AS PlatformCount FROM games GROUP BY Publisher HAVING PlatformCount >= 3;
-- Esercizio 23
select Original_platform, year, count(*) as totale from games group by Original_platform, year having totale > 5 order by year;
-- Esercizio 24
select game, length(genre) - length(replace(genre,',','')) +1 as genrecount from games having genrecount > 1;
-- Esercizio 25
select publisher ,count(*) as numero, genre from games group by genre, publisher having numero = (select max(pubcount) from (select genre, publisher, count(*) as pubcount from games group by genre, publisher) as subquery where subquery.genre = games.genre order by genre desc);
-- Esercizio 26
select Original_platform, game, year from games where (Original_platform, year) in (select Original_platform, min(year) from games group by Original_platform);
-- Esercizio 27
select game from games where game in (select game from games group by game having count(distinct genre)>1 or count(distinct publisher)> 1);
-- Esercizio 28
select genre, count(*) as 'totale_giochi', round(count(*) *100 / (select count(*) from games), 2) as percentuale from games group by genre;
-- Esercizio 29
SELECT Publisher, COUNT(*) AS TotalGames, 
       RANK() OVER (ORDER BY COUNT(*) DESC) AS posizione
FROM games
GROUP BY Publisher;
-- Esercizio 30


SELECT 
year, 
Genre,
COUNT(*) AS TotalGames,
       RANK() OVER (PARTITION BY year ORDER BY COUNT(*) DESC) AS posizione
FROM gamesgames
GROUP BY year, Genre
ORDER BY year, posizione;
-- tester 
select * from games where game like '%god%';











































