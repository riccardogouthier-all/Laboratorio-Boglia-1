import random

def number_guessing_game():
    print("🔢 GIOCO INDOVINA IL NUMERO 🔢")

    # 1. Genera il numero segreto
    min = 1
    max = 100
    sec = random.randint(min, max)

    tentativi = 0
    indovinato = False

    print(f"Ho pensato a un numero tra {min} e {max}.")

    # 2. Ciclo principale del gioco
    while not indovinato:
        try:
            tentativo_utente = int(input("Indovina il numero: "))
            tentativi += 1

            if tentativo_utente < min or tentativo_utente > max:
                print(f"Per favore, inserisci un numero tra {min} e {max}.")
                continue

            # 3. Controllo del numero e suggerimenti
            if tentativo_utente < sec:
                print("⬆️ Troppo basso! Riprova.")
            elif tentativo_utente > sec:
                print("⬇️ Troppo alto! Riprova.")
            else:
                indovinato = True
                print("\n" + "="*40)
                print(f"🎉 COMPLIMENTI! Hai indovinato il numero {sec}!")
                print(f"Hai impiegato {tentativi} tentativi.")
                print("="*40)

        except ValueError:
            print("❌ Devi inserire un numero intero valido.")

number_guessing_game()