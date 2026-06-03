'''
Scrivere un programma che, leggendo da tastiera una stringa, la salvi su file “stringa.txt”. Successivamente aprire il file “stringa.txt” e verificare il salvataggio. 
'''


stringa = input("Inserisci una stringa: ")

if stringa.strip() == "":
    print("Attenzione: hai inserito una stringa vuota. Il file sarà creato ma con contenuto vuoto.")

with open("stringa.txt", "w", encoding="utf-8") as file:
    file.write(stringa)

print(f'\n Stringa salvata correttamente nel file "stringa.txt".')

with open("stringa.txt", "r", encoding="utf-8") as file:
    contenuto = file.read()

print(f' Contenuto letto dal file: "{contenuto}"')

if contenuto == stringa:
    print(" Verifica superata: la stringa letta corrisponde a quella salvata.")
else:
    print(" Errore: la stringa letta NON corrisponde a quella salvata.\n")
