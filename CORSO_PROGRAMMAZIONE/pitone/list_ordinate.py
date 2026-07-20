from dataclasses import dataclass

@dataclass
class Libro:
    titolo : str
    pagine : int


libri = [
    Libro('A nord di Budapesht', 500),
    Libro('E anche oggi vinco domani', 300),
    Libro('La soddisfazione dell anima', 240)
]

def ordinatore_titolo(libro):
    return libro.titolo

libri.sort(key=ordinatore_titolo)


def ordinatore_pagine(libro):
    return libro.pagine

# libri.sort(key=ordinatore_pagine)

libri.sort(key=lambda libro:libro.pagine)


print(libri)



# parole = ['pisolo', 'eolo', 'bontolo', 'mammolo', 'gongolo', 'cucciolo', 'dotto']
# parole.sort()
# print(parole)

# daordinare = [25,28,24,27,29]
# daordinare.sort()

# ordinati = []

# voti = [25,28,24,27,29,30,18,25]
# voti.sort()
# print(voti)


