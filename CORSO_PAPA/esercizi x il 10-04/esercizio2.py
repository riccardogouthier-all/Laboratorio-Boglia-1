'''  
Autore:  Riccardo Gouthier     
Data: 26/03/2026     
Titolo: 
Creare una funzione che abbia come parametri formali un numero arbitrario di valori numerici. 
Si vuole che restituisca la somma dei soli numeri pari e il prodotto dei soli numeri dispari. 
Successivamente creare un programma che richiami tale funzione e che stampi in output i risultati. 
No standard input. 
'''

"""funzione con x numeri"""
"""somma if int/2 = int :: prodotto if int/2 != int"""
"""main(somma() prodotto() print(somma prodotto))"""
"""no dati salvati in memoria"""


"""
- "*args" permette di passare un numero qualsiasi di valori alla funzione
- Il ciclo `for` controlla ogni numero: se è **pari** (`n % 2 == 0`) lo aggiunge alla somma, altrimenti lo moltiplica al prodotto
- Il flag `ci_sono_dispari` serve per gestire il caso in cui non ci siano dispari (prodotto rimane 0 invece di 1)
- Il programma principale legge i numeri da tastiera e richiama la funzione
"""

def analizza_numeri(*args):
    """
    Riceve un numero variabile di valori numerici.
    Restituisce la somma dei pari e il prodotto dei dispari.
    """
    somma_pari = 0
    prodotto_dispari = 1
    ci_sono_dispari = False

    for n in args:
        if n % 2 == 0:
            somma_pari += n
        else:
            prodotto_dispari *= n
            ci_sono_dispari = True

    if not ci_sono_dispari:
        prodotto_dispari = 0

    return somma_pari, prodotto_dispari

def leggi_numeri():
    """
    Legge e valida l'input dell'utente.
    Accetta solo numeri interi separati da spazio.
    """
    while True:
        print("Inserisci i numeri da analizzare (separati da spazio):")
        input_utente = input("> ").strip()

        # Controlla che non sia vuoto
        if not input_utente:
            print("Input vuoto. Inserisci almeno un numero.\n")
            continue

        valori = input_utente.split()
        numeri_validi = []
        errore = False

        for valore in valori:
            try:
                numeri_validi.append(int(valore))
            except ValueError:
                print("E' presente un carattere numerico o simbolico non valido. Reinserisci gli input.\n")
                errore = True
                break

        if not errore:
            return numeri_validi

# --- Programma principale ---
def main():
    numeri = leggi_numeri()
    somma, prodotto = analizza_numeri(*numeri)

    print(f"\nNumeri inseriti: {numeri}")
    print(f"Somma dei pari: {somma}")
    print(f"Prodotto dei dispari: {prodotto}")

if __name__ == "__main__":
    main()