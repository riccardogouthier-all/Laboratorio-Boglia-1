'''  
Autore:  Riccardo Gouthier     
Data: 26/03/2026     
Titolo: 
Conversione temperatura: implementare una funzione convertiCF che converta una 
temperatura espressa in gradi Fahrenheit in una temperatura espressa in gradi Celsius. 
Usare la seguente formula: C = (F   - 32) * 5 / 9 
Creare un programma principale che richiami la funzione e ne stampi il risultato
visualizzando solo 3 cifre decimali. 
'''
def fahrenheit():
    """ ciclo per controllare se il numero inserito per le ore non è negativo o un valore alfabetico """
    g = input("Inserisci qui i gradi Fahrenheit: ")
    while not g.lstrip('-.').isdigit():
        g = input("Inserisci qui il NUMERO di Fahrenheit CORRETTO (FORMATO NUMERICO): ")
        return fahrenheit()
    cels = float(g)
    return cels    

def conversione(F):
    C = (F   - 32) * 5 / 9
    return C

def main():
    fahr = fahrenheit()
    celsius = conversione(fahr)
    print(f"hai inserito {fahr:.3f} fahrenheit, cioè {celsius:.3f} Celsius")

if __name__ == "__main__":
    main()

# metodo per gestire gli input

# metodo per calcolare il numero di secondi dagli input

# Inizializzazioni variabili

# Assegnazione valori dopo il calcolo dei secondi

# Ciclo per confrontare i valori + selezione output
