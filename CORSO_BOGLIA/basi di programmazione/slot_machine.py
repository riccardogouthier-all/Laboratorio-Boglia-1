import random

def spin():
    symbols = ['👽','❤️','🍕','🍋','🥕']
    riga = []
    for x in range(3):
        riga.append(random.choice(symbols))
    return riga

def print_row(riga):
    print("*" *20)
    print(" | ".join(riga))
    print("*" *20)

def check(riga, puntata):
    if riga[0] == riga[1] == riga[2]:
        if riga[0] == '👽':
            return puntata * 2
        elif riga[0] == '❤️':
            return puntata * 4
        elif riga[0] == '🍕':
            return puntata * 6
        elif riga[0] == '🍋':
            return puntata * 10
        elif riga[0] == '🥕':
            return puntata * 20
    return 0

def main():
    credits = int(input("quanto vuoi caricare?"))
    print("-----------------------")
    print("Gioco Pitonico")
    print("-----------------------")

    while credits > 0:
        puntata = input(f"Quanto vuoi puntare? (1 - {credits})")
        if not puntata.isdigit():
            print("Inserisci un valore numerico tra 1 e 100")
            continue
        puntata = int(puntata)
        if puntata <= 0:
            print("La puntata deve essere maggiore di 0")
            continue
        if puntata > credits:
            print(f"Tu hai {credits} crediti, non puoi puntare {puntata} crediti")
            continue
        credits -= puntata
        riga = spin()
        print_row(riga)
        punteggio = check(riga, puntata)

        credits += punteggio

        if punteggio > 0:
            print(f"Complimenti hai vinto {punteggio} crediti")
        else:
            print("Mi dispiace non hai vinto. Ritenta!")

        print(f"Credito residuo {credits} crediti")

        play_again = input("Vuoi uscire?").upper()

        if play_again == 'Y':
            break

print("Game Over!")

if __name__=="__main__":
    main()
