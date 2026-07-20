 SELECT * FROM alimenti;

 SELECT * FROM alimenti WHERE categoria = 'carne';

 SELECT COUNT(*) AS numero_alimenti FROM alimenti;

 SELECT * FROM alimenti WHERE proteine > 10;

 SELECT * FROM alimenti ORDER BY energia DESC LIMIT 5;

 SELECT AVG(proteine) AS mediaproteine FROM alimenti WHERE categoria = 'carne';

 SELECT * FROM alimenti where carboidrati=0;

 SELECT * FROM alimenti order by lipidi desc;

 SELECT categoria, COUNT(*) AS numero_di_alimenti 
 FROM alimenti 
 GROUP BY categoria;

 SELECT * FROM alimenti where carboidrati BETWEEN 10 and 30;




SELECT COUNT(*) AS totale_cibo FROM alimenti;

SELECT AVG(proteine) AS media_proteine FROM alimenti;

SELECT MAX(energia) AS energia_max, MIN(energia) AS energia_min FROM alimenti;

SELECT SUM(lipidi) AS totale_lipidi FROM alimenti;

SELECT categoria, COUNT(*) AS totale_alimenti 
FROM alimenti 
GROUP BY categoria;

SELECT categoria, AVG(carboidrati) AS media_carboidrati 
FROM alimenti 
GROUP BY categoria;

SELECT categoria, AVG(energia) AS kcal_medie 
FROM alimenti 
GROUP BY categoria 
ORDER BY kcal_medie DESC LIMIT 1;

SELECT prodotto, proteine
FROM alimenti 
WHERE proteine = (SELECT MAX(proteine) FROM alimenti);

SELECT categoria, SUM(energia) as totale_kcal
from alimenti
group by categoria;

SELECT COUNT(*) AS alimenti_molto_proteici 
FROM alimenti 
WHERE proteine > 10;
