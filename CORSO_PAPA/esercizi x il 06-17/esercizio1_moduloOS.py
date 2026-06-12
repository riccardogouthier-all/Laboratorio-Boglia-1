'''
Scrivere una procedura che dato un percorso elenchi tutte le directories presenti.
'''

import os
from pathlib import Path

def elencare_directories(percorso):
    """
    Procedura che dato un percorso elencta tutte le directories presenti.
    
    Args:
        percorso: stringa con il percorso della directory da esplorare
        
    Returns:
        lista di nomi delle directory trovate
    """
    # Verifica che il percorso esiste e è una directory
    # if not Path(percorso).exists:
    if not os.path.exists(percorso):
        print(f"Errore: il percorso '{percorso}' non esiste.")
        return []
    
    if not os.path.isdir(percorso):
        print(f"Errore: '{percorso}' non è una directory.")
        return []
    
    # Elenca tutti gli elementi nel percorso e filtra solo le directory
    directories = []
    
    for elemento in os.listdir(percorso):
        # Costruisce il percorso completo per verificare se è una directory
        percorso_completo = os.path.join(percorso, elemento)
        
        if os.path.isdir(percorso_completo):
            directories.append(elemento)
    
    # Elenca le directory trovate
    if directories:
        print(f"Directory trovate in '{percorso}':")
        for i, dir_name in enumerate(directories, 1):
            print(f"  {i}. {dir_name}")
    else:
        print(f"Nessuna directory trovata in '{percorso}'.")
    
    return directories

# Esempio di utilizzo
if __name__ == "__main__":
    # Test con il percorso corrente (.)
    percorso_test = "."
    
    directories_trovate = elencare_directories(percorso_test)
    
    print(f"\nTotale directory trovate: {len(directories_trovate)}")