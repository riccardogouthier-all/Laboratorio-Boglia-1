'''  
Autore:  Riccardo Gouthier     
Data: 26/03/2026     
Titolo: 
Creare una funzione che abbia come parametri formali un numero arbitrario di valori numerici. 
Si vuole che restituisca la somma dei soli numeri pari e il prodotto dei soli numeri dispari. 
Successivamente creare un programma che richiami tale funzione e che stampi in output i risultati. 
No standard input. 
'''

def analizza_numeri(*numeri):
    """Riceve un numero variabile di valori numerici. Restituisce la somma dei pari e il prodotto dei dispari."""
    somma_pari = 0
    prodotto_dispari = 1
    ci_sono_dispari = False

    for n in numeri:
        if n % 2 == 0:
            somma_pari += n
        else:
            prodotto_dispari *= n
            ci_sono_dispari = True

    if not ci_sono_dispari:
        prodotto_dispari = 0

    return somma_pari, prodotto_dispari

# def leggi_numeri():
#     """Legge e valida l'input dell'utente. Accetta solo numeri interi separati da spazio."""
#     print("Inserisci i numeri da analizzare (separati da spazio):")
#     input_utente = input("> ").strip()
#     """Controlla che non sia vuoto"""
#     if not input_utente:
#         print("Input vuoto. Inserisci almeno un numero.\n")
#         return leggi_numeri()
    
#     valori = input_utente.split()
    
#     if not all(v.lstrip('-').isdigit() for v in valori):
#         print("E' presente un carattere non numerico o simbolico non valido. Reinserisci gli input.")
#         return leggi_numeri()
    
#     return list(map(int, valori))
    
"""Programma principale"""
def main():
    numeri = (1,2,3,4,5,6,7,8,9)
    # numeri = leggi_numeri()
    somma, prodotto = analizza_numeri(*numeri)

    print(f"Numeri inseriti: {numeri}")
    print(f"Somma dei pari: {somma}")
    print(f"Prodotto dei dispari: {prodotto}")

if __name__ == "__main__":
    main()