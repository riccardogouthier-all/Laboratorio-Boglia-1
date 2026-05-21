
nome = input("Inserisci il tuo nome: ")

primi = 0
secondi = 0
bibite = 0  # bibite non acqua

while True:
    print(f"\n{nome}, scegli il prodotto che vuoi ordinare:")
    print("1. Primo 5€")
    print("2. Secondo 4€")
    print("3. Bibita (non acqua) 0.50€")
    print("0. Fine ordine")

    scelta = input("Inserisci il numero dell'opzione: ")

    # try/except per gestire input non numerici
    try:
        scelta = int(scelta)
    except ValueError:
        print("Errore: devi inserire un numero (0, 1, 2 o 3).")
        continue

    if scelta == 1:
        primi += 1
        print(f"Hai aggiunto un primo. Totale primi: {primi}")
    elif scelta == 2:
        secondi += 1
        print(f"Hai aggiunto un secondo. Totale secondi: {secondi}")
    elif scelta == 3:
        quantita = input("Quante bibite (non acqua) vuoi aggiungere? ")
        try:
            quantita = int(quantita)
            if quantita < 0:
                print("La quantità non può essere negativa.")
                continue
            bibite += quantita
            print(f"Hai aggiunto {quantita} bibite. Totale bibite: {bibite}")
        except ValueError:
            print("Errore: la quantità deve essere un numero intero.")
        # dopo le bibite torniamo al menu senza uscire
        continue
    elif scelta == 0:
        # fine ordine
        break
    else:
        print("Opzione non valida. Scegli 0, 1, 2 o 3.")
        continue

# Calcolo dei costi
costo_primi = 0.0
if primi > 0:
    cstp = 5.0
    if primi == 1:
        costo_primi = cstp
    else:
        costo_primi = cstp + (primi - 1) * cstp * 0.8

# Secondi: 4€ ciascuno
costo_secondi = secondi * 4.0

# Bibite non acqua: 0.50€ ciascuna
costo_bibite = bibite * 0.50

# Acqua è gratis: non serve conteggiarla, il costo è 0
costo_totale = costo_primi + costo_secondi + costo_bibite

print(f"\n{nome} - Totale pranzo: {costo_totale:.2f} euro")