
nome = input("Inserisci il tuo nome: ").strip()
 
while True:
    ore_input = input("Numero di ore di utilizzo (intero > 0): ").strip()
    if ore_input.isdigit() and int(ore_input) > 0:
        ore = int(ore_input)
        break
    print("Errore: inserisci un numero intero maggiore di 0.")
 
while True:
    try:
        costo_orario = float(input("Costo orario (euro, > 0): "))
        if costo_orario > 0:
            break
        print("Errore: il costo deve essere maggiore di 0.")
    except ValueError:
        print("Errore: inserisci un numero valido (es. 0.50).")
 
totale = ore * costo_orario
 
if ore > 100:
    totale *= 0.90
 
print(f"{nome} - costo totale VM: {totale:.2f} euro")

