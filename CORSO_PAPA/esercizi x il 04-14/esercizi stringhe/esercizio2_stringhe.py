''' 
Secondo Esercizio 
Scrivere un programma che dica se una stringa è palindroma. 
Esempio: 
str="ABBA" PALINDROMA 
str="PIPPO" NON PALINDROMA 
'''



def e_palindormo(parola):
    stringa = parola.lower().replace(" ","").replace("'","")
    agnirts = stringa[::-1]
    return bool(stringa == agnirts)

stringa = "Ai lati d'Italia"

if e_palindormo(stringa):
    print(f"{stringa} E' PALINDROMO")
else:
    print(f"{stringa} NON E' PALINDROMO")