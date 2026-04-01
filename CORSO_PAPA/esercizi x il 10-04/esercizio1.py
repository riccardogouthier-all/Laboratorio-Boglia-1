'''  
Autore:  Riccardo Gouthier     
Data: 23/03/2026     
Titolo: 
Creare una funzione che riceva una quantità di tempo in formato ore, minuti e secondi e la restituisca espressa solamente in secondi. 
Successivamente creare un programma principale che chieda in input due quantità di tempo e stampi in output quale quantità di tempo è maggiore. 
La funzione deve avere i parametri formali con valori predefiniti. 
''' 

def calcolo_secondi(ore, minuti, secondi):              
    """metodo per calcolare l'output (numero di secondi) dagli input(ore, minuti, secondi)"""
    tot = ore * 3600 + minuti * 60 + secondi
    return tot

def controllo_tempi(tempo1, tempo2):
    """ metodo per controllare quale dei due tempi è maggiore, funziona con due valori passati dal codice e li mette a confronto
    i valori in ingresso possono essere in storage macchina o due input. """
    tot1 = tempo1
    tot2 = tempo2

    if tot1 > tot2:                                                         
        print(f"L'input maggiore è il numero 1:: | {tot1} |")
    elif tot1 < tot2:
        print(f"L'input maggiore è il numero 2:: | {tot2} |")
    else:
        print(f"I due input sono uguali::| {tot1} | {tot2} |")

def inserimento_tempi():           
    """    metodo per gestire gli input"""

    def manuale_ore():
        """ ciclo per controllare se il numero inserito per le ore non è negativo o un valore alfabetico """
        a = input("Inserisci qui il numero di ore: ")
        while not a.isdigit():
            a = input("Inserisci qui il NUMERO di ore CORRETTO (FORMATO NUMERICO): ")
        ore = int(a)
        return ore
    b_ore = manuale_ore()

    def manuale_minuti():
        """ ciclo per controllare se il numero inserito per i minuti non è negativo o un valore alfabetico o se è maggiore di 59"""
        b = input("Inserisci qui il numero di minuti: ")
        while not b.isdigit():
            b = input("Inserisci qui il NUMERO di minuti CORRETTO (FORMATO NUMERICO): ")
        minuti = int(b)
        if not minuti < 60:
            minuti = 0
            print("Valore di riferimento dei minuti non valido, inserire un range fino a 59")
            return manuale_minuti()
        return minuti
    b_minuti = manuale_minuti()

    def manuale_secondi():
        """ ciclo per controllare se il numero inserito per i secondi non è negativo o un valore alfabetico o se è maggiore di 59"""
        c = input("Inserisci qui il numero di secondi: ")
        while not c.isdigit():
            c = input("Inserisci qui il NUMERO di secondi CORRETTO (FORMATO NUMERICO): ")
        secondi = int(c)
        if not secondi < 60:
            secondi = 0
            print("Valore di riferimento dei secondi non valido, inserire un range fino a 59")
            return manuale_secondi()
        return secondi
    b_secondi = manuale_secondi()

    return b_ore, b_minuti, b_secondi 

def main():

    ore1 ,minuti1, secondi1 = inserimento_tempi()
    tot1 = calcolo_secondi(ore1, minuti1, secondi1) 
    """ Dopo aver usato i metodi per inizializzare le variabili  """     
    risposta1 = input("Vuoi inserire un primo orario da comparare? (y/N) PPURE premi z per compararlo con il numero in storage: ")
    if risposta1.capitalize() == "Y":
        ore2 ,minuti2, secondi2 = inserimento_tempi()
        tot2 = calcolo_secondi(ore2, minuti2, secondi2)    
        return controllo_tempi(tot1, tot2)
    elif risposta1.capitalize() != "Y" and risposta1.capitalize() != "Z":
        """  """
        tot2 = 0
        print("non stai comparando il numero con nessuno dato")
        return controllo_tempi(tot1, tot2)
    elif risposta1.capitalize() == "Z":
        """  """
        tot2 = 10000
        return controllo_tempi(tot1, tot2)                      

if __name__ == "__main__":
    main()
# Stampa di prova
# print(f"Prova di stampa per 1: {tot1}   2: {tot2}")