'''
Scrivere un programma che permetta di copiare il contenuto di un file in un altro file. 
'''

def copia_file(file_sorgente, file_destinazione):
    with open(file_sorgente, 'r', encoding='utf-8') as sorgente:
        contenuto = sorgente.read()

    with open(file_destinazione, 'w', encoding='utf-8') as destinazione:
        destinazione.write(contenuto)

    print(f"Contenuto copiato da '{file_sorgente}' a '{file_destinazione}' con successo!")

partenza = "filepartenza.txt"
destinazione = "filearrivo.txt"

try:
    copia_file(partenza, destinazione)
except FileNotFoundError:
    print(f"Errore: il file di partenza '{partenza}' non esiste.")
