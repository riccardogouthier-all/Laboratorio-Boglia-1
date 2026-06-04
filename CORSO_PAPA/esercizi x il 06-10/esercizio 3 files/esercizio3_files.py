'''
Progetta una classe che legga un file di testo. Tale classe deve avere un metodo che restituisca la parola con frequenza maggiore. 

[Suggerimento: si consideri l'esercizio che contava le frequenze delle lettere in una stringa utilizzando i dictionary] 

Provare il programma con testi classici come la Divina Commedia di Dante Alighieri reperibile sul sito del progetto Gutenberg. 
'''

class LettoreTestoFile:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read_file(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parola_con_frequenza_massima(self):
        testo = self.read_file()
        
        testo_pulito = ''
        for char in testo.lower():
            if char.isalpha() or char.isspace():
                testo_pulito += char
            else:
                testo_pulito += ' '
        
        parole = testo_pulito.split()
        
        frequenza_parole = {}
        for parola in parole:
            if parola:
                frequenza_parole[parola] = frequenza_parole.get(parola, 0) + 1
        
        if not frequenza_parole:
            return ("Il file è vuoto o non contiene parole.")
        else:        
            parola_max = max(frequenza_parole, key=frequenza_parole.get)
            return (f"La parola con frequenza maggiore è: {parola_max} con frequenza {frequenza_parole[parola_max]}")

DDDDDDDDDDDD = "prova.txt"

if DDDDDDDDDDDD:
    lettore = LettoreTestoFile(DDDDDDDDDDDD)
    print(lettore.parola_con_frequenza_massima())

# La classe:
# __init__: salva il percorso del file
# read_file(): legge e restituisce il contenuto del file
# parola_con_frequenza_massima():
# Pulisce il testo (minuscolo, rimuove punteggiatura)
# Conta le frequenze delle parole con un dizionario
# Restituisce la parola più frequente
# La variabile DDDDDDDDDDD è dichiarata ma non inizializzata, pronta per essere_ASSIGNATA da te successivamente con il percorso del file.
# il filepath è il nome del file che metterai nella stessa cartella del programma o il percorso completo se si trova altrove.