nome =  input("Inserisci il tuo nome: ")

while True:
    try:
        n = int(input("Inserisci la dimensione della scacchiera (n x n): "))
        while n <= 0:
            print("Per favore, inserisci un numero positivo.")
            n = int(input("Inserisci la dimensione della scacchiera (n x n): "))
        c = input("Inserisci il carattere da usare per le caselle colorate: ")
        while len(c) != 1:
            print("Per favore, inserisci un solo carattere.")
            c = input("Inserisci il carattere da usare per le caselle colorate: ")
        break
    except ValueError:
        print("Per favore, inserisci un numero valido.")
    
print(f"\nScacchiera generata da: {nome}:\n")

for i in range(n):
    for j in range(n):
        if (i + j) % 2 == 0:
            print(c, end=" ")
        else:
            print("_", end=" ")
    print()