'''
Quarto Esercizio 
Scrivere un programma per contare gli elementi in una lista finché non si incontra un elemento di tipo tupla. 
[Suggerimento: si usi la funzione isinstance()] 
'''



lista = [ "a" , 1 , ["a","b","c"] , "a"  , ["a","b","c"] , 1 , "a" , ("LA TUPLA SONO IO",4) , ["a","b","c"] , 1 , "a" , ["a","b","c"] , 1 , ["a","b","c"] , "a" , 1 , "a" , 1 ]
print(lista)

def spulcia_lista(lista):
    contatore = 0
    for elemento in lista:
        if isinstance(elemento, tuple):
            break
        contatore += 1
    return contatore

elementi = spulcia_lista(lista= lista)

if elementi == len(lista):
    print(f"Nella lista non sono presenti elementi di tipo tupla e contiene {len(lista)} elementi.")
else:       
    print(f"Nella lista ci sono {elementi} elementi prima di incontrare una tupla")



