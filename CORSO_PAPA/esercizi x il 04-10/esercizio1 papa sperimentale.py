
"""
    Autore: Alessandro Verduna
    Data: 20/03/2026
    
    Consegna: Primo Esercizio
        Creare una funzione che riceva una quantità di tempo in formato ore, minuti e secondi e la
        restituisca espressa solamente in secondi. Successivamente creare un programma
        principale che chieda in input due quantità di tempo e stampi in output quale quantità di
        tempo è maggiore. La funzione deve avere i parametri formali con valori predefiniti.
"""

def return_time_in_seconds(ore, minuti, secondi):

    return ore * 3600 + minuti * 60 + secondi

def bigger_time_given(ora_a = 1, minuti_a = 40, secondi_a = 20, ora_b = 2, minuti_b = 50, secondi_b = 11):
   
    totale1 = return_time_in_seconds(ora_a, minuti_a, secondi_a)
    totale2 = return_time_in_seconds(ora_b, minuti_b, secondi_b)

    if totale1 > totale2:
        return "Il primo orario è maggiore"
    elif totale1 == totale2:
        return "I due orari sono uguali"
    else:
        return "Il secondo orario è maggiore"

def input_and_validation():
    
    """
    Consente di inserire l'input in formato ore, minuti, secondi verificando anche la validità dei dati inseriti
    e li richiede all'utente qual'ora fossero errati.
    Parametri:
        NONE
    Ritorna:
        input_ore (int): dato validato corrispondente al numero di ore
        input_minuti (int:): dato validato corrispondente al numero di minuti
        input_secondi (int): dato validato corrispondente al numero di secondi
    """
    correttezza_input = False
    while correttezza_input != True:

        def manuale_ore():
            input_ore_str = input("Inserisci qui il numero di ore: ")
            while not input_ore_str.isdigit():
                input_ore_str = input("Inserisci qui il NUMERO di ore CORRETTO: ")
            ore = int(input_ore_str)
            return ore
        b_ore = manuale_ore()

        def manuale_minuti():
            input_minuti_str = input("Inserisci qui il numero di minuti: ")
            while not input_minuti_str.isdigit():
                input_minuti_str = input("Inserisci qui il NUMERO di minuti CORRETTO: ")
            minuti = int(input_minuti_str)
            return minuti
        b_minuti = manuale_minuti()

        def manuale_secondi():
            input_secondi_str = input("Inserisci qui il numero di secondi: ")
            while not input_secondi_str.isdigit():
                input_secondi_str = input("Inserisci qui il NUMERO di secondi CORRETTO: ")
            secondi = int(input_secondi_str)
            return secondi
        b_secondi = manuale_secondi()

        if not 0 < b_minuti < 60:
            print("Valore di riferimento dei minuti non valido")
            manuale_minuti()

        if not b_secondi < 60:
            print("Valore di riferimento dei secondi non valido")
            manuale_secondi()
        else:
            correttezza_input = True
    return b_ore, b_minuti, b_secondi 

def main():   
   
    a, b, c = input_and_validation()
    totale1 = return_time_in_seconds(a, b, c)        
    print(f"L'orario fornito equivale a: {totale1} secondi")

    risposta1 = input("Vuoi inserire un primo orario da comparare? (Y/N) ")
    risposta2 = input("Vuoi inserire un secondo orariod a comparare? (Y/N) ")

    if risposta1.capitalize() == "Y" and risposta2.capitalize() == "Y":
        a, b, c = input_and_validation()
        d, e, f = input_and_validation()
        print(bigger_time_given(a, b, c, d, e, f))
    elif risposta1.capitalize() == "Y" and risposta2.capitalize() != "Y":
        a, b, c = input_and_validation()
        print(bigger_time_given(a, b, c))
    elif risposta1.capitalize() != "Y" and risposta2.capitalize() == "Y":
        d, e, f = input_and_validation()
        print(bigger_time_given(ora_b = d, minuti_b = e, secondi_b = f))
    else:
        print(bigger_time_given())

if __name__ == "__main__":
    main()