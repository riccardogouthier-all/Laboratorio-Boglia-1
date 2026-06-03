'''
Progetta una classe che legga un file di testo. Tale classe deve avere un metodo che restituisca la parola con frequenza maggiore. 

[Suggerimento: si consideri l'esercizio che contava le frequenze delle lettere in una stringa utilizzando i dictionary] 

Provare il programma con testi classici come la Divina Commedia di Dante Alighieri reperibile sul sito del progetto Gutenberg. 
'''

class FileTextReader:
    def __init__(self, filepath):
        """Inizializza con il percorso del file di testo"""
        self.filepath = filepath
    
    def read_file(self):
        """Legge il contenuto del file e restituisce una stringa"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parola_con_frequenza_massima(self):
        """
        Restituisce la parola con frequenza maggiore nel file.
        Usa un dizionario per contare le frequenze delle parole.
        """
        testo = self.read_file()
        
        # Normalizza il testo: minuscolo e rimuove punteggiatura
        testo_pulito = ''
        for char in testo.lower():
            if char.isalpha() or char.isspace():
                testo_pulito += char
            else:
                testo_pulito += ' '
        
        # Dividi in parole
        parole = testo_pulito.split()
        
        # Conta le frequenze delle parole usando un dizionario
        frequenza_parole = {}
        for parola in parole:
            if parola:  # evita stringhe vuote
                frequenza_parole[parola] = frequenza_parole.get(parola, 0) + 1
        
        # Trova la parola con frequenza massima
        if not frequenza_parole:
            return None
        
        parola_max = max(frequenza_parole, key=frequenza_parole.get)
        return parola_max


# Struttura per provare la classe (variabile DDDDDDDDDDDD non inizializzata)
# DDDDDDDDDDDD =  # La inizializzerai tu a posteriori

# Esempio di utilizzo (commentato, da sbloccare quando inizializzi DDDDDDDDDDDD):
# if DDDDDDDDDDDD:
#     lettore = FileTextReader(DDDDDDDDDDD)
#     risultato = lettore.parola_con_frequenza_massima()
#     print(f"La parola con frequenza maggiore è: {risultato}")

# La classe:
# __init__: salva il percorso del file
# read_file(): legge e restituisce il contenuto del file
# parola_con_frequenza_massima():
# Pulisce il testo (minuscolo, rimuove punteggiatura)
# Conta le frequenze delle parole con un dizionario
# Restituisce la parola più frequente
# La variabile DDDDDDDDDDD è dichiarata ma non inizializzata, pronta per essere_ASSIGNATA da te successivamente con il percorso del file.
# il filepath è il nome del file che metterai nella stessa cartella del programma o il percorso completo se si trova altrove.