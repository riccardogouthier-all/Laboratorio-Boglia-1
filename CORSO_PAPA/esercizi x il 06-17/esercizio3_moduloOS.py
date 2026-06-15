'''
Scrivere un programma Python per eseguire un comando del sistema operativo usando il modulo os.
'''

import os

if __name__ == "__main__":
    comando = input("Inserisci il comando da eseguire: ")
    os.system(comando)