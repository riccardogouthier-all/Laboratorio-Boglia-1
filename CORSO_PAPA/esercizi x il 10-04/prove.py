def fahrenheit():
    """ ciclo per controllare se il numero inserito per le ore non è negativo o un valore alfabetico """
    g = input("Inserisci qui i gradi Fahrenheit: ")






    
    if g.count('.') == 1:
        g_nop = g.replace('.', '')
    elif g.count('.') == 0:
        g_nop = g
    else:
        print("Inserisci NUMERO di Fahrenheit col formato corretto -x.yyy : ")
        fahrenheit()
    """"""

    
        
    while not g_nom.lstrip('-').isdigit():
        g = input("Inserisci qui il NUMERO di Fahrenheit CORRETTO (FORMATO NUMERICO): ")
        return fahrenheit()    


    cels = float(g)
    return cels   

print(f"{fahrenheit()}")