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
    if g.count('.') == 1:
        g_nop = g.replace('.', '')
    elif g.count('.') == 0:
        g_nop = g
    else:
        print("Inserisci NUMERO di Fahrenheit col formato corretto -+xxx.yyy")
        return fahrenheit()

    segno = g_nop.count('+') + g_nop.count('-')
    if segno > 1 or (segno == 1 and not (g_nop.startswith('+') or g_nop.startswith('-'))):
        print("Hai inserito troppo segni davanti al valore numerico")
        return fahrenheit()

    """"""
    while not g_nop.lstrip('-').lstrip('+').isdigit():
        print("Inserisci il NUMERO di Fahrenheit CORRETTO (FORMATO NUMERICO)")
        return fahrenheit()

    cels = float(g)
    return cels    

def conversione(f):
    """"""
    return (f - 32) * 5 / 9

def main():
    """"""
    f = fahrenheit()
    celsius = conversione(f)
    print(f"hai inserito {f:.3f} fahrenheit, cioè {celsius:.3f} Celsius")

if __name__ == "__main__":
    """"""
    main()
