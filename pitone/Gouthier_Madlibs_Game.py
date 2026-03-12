# Madlibs Game - Storia divertente
print("🎭 BENVENUTO AL GIOCO MADLIBS! 🎭")
print("Inserisci le parole richieste per creare una storia divertente!\n")


nomi = ["Alice", "Marco", "Giulia", "Luca"]

# Raccolta input
nome = input("Inserisci un nome: ")
aggettivo1 = input("Inserisci un aggettivo: ")
animale = input("Inserisci un animale: ")
cibo = input("Inserisci un cibo: ")
numero = input("Inserisci un numero: ")
colore = input("Inserisci un colore: ")
verbo = input("Inserisci un verbo: ")



# Controllo dei nomi
if nome.lower() in [n.lower() for n in nomi]:

    # Creazione della storia
    storia = f"""
🌟 LA STORIA DI {str(nome).upper()} 🌟

C'era una volta {nome}, una persona molto {aggettivo1}.
Un giorno, mentre camminava nel bosco, incontrò un {animale} {colore}.
L'animale aveva {numero} pezzi di {cibo} e voleva {verbo}.
{nome} decise di aiutarlo e insieme vissero felici e contenti!
"""

    print(storia)

else:
    print(f"{nome} non è presente nella lista.")


