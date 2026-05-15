'''
Autore: Riccardo Gouthier
Data: 08/03/2026
Titolo: Leggere una successione di numeri interi passati dall utente, fermandosi al primo numero
che rende la successione non crescente e restituendo quanti numeri formano la successione inserita.
'''

# Inizializzazioni variabili
y = 0
x = 0
n_crescenti = 0
valore_precedente = 0.0

# Sezione di input Dati
while y == 0:
    try:
        while x <= 0:
            x = int(input("Quanti valori vuoi inserire:\n"))

        lista = []

        for i in range(x):
            num = float(input(f"Inserire il n: {i+1} \n"))
            lista.append(num)

        y = 1
    except ValueError:
            print("Errore: inserisci numeri validi!, per punizione ri inizia da capo")
    except IndexError:
            print("Errore: indici fuori range!, per punizione ri inizia da capo")
    except ZeroDivisionError:
            print("Errore: intervallo vuoto!, per punizione ri inizia da capo")
    except:
            print("Altro errore!, non e' colpa tua ma comunque ri inizia da capo")

# Elaborazione
valore_precedente = lista[0] - 1

for i in range(len(lista)):
    
    if valore_precedente < lista[i]:
            n_crescenti += 1
            valore_precedente = lista[i]
    else:
          break

# Eventuali sotto processi di Elaborazione

# Sezione di output
print(f"il numero di valori crescenti continui nella tua lista sono {n_crescenti}")