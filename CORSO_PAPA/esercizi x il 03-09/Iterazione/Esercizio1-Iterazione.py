'''
Autore: Riccardo Gouthier
Data: 08/03/2026
Titolo: Si hanno in input due numeri reali A e B e una successione di numeri reali positivi che
termina con il valore 0. Si vuole in output la media dei soli numeri compresi tra A e B.
'''

# Inizializzazioni variabili
y = 0
media = 0
n = 0
x = 0
n_media = []

# Sezione di input Dati
while y == 0:
    try:
        while x <= 0:
            x = int(input("Quanti valori vuoi inserire:\n"))

        lista = []

        for i in range(x):
            num = float(input(f"Inserire il n: {i+1} \n"))
            lista.append(num)

        lista.append(0)
        print("Lista completa:", lista)

        a = float((input("Inserisci il primo valore da trovare tra quelli della lista \n")))
        b = float((input("Inserisci il secondo valore da trovare tra quelli della lista \n")))

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
if a > b:
    c = a
    a = b
    b = c

for i in range(len(lista) - 1):
    if a <= lista[i] and b >= lista[i]:
        media += lista[i]
        n_media.append(lista[i])
        n += 1

# Eventuali sotto processi di Elaborazione
if n != 0:
    c = media / n
else:
    c = 0

# Sezione di output
print(f"La media e' {c} perche la media di {n_media} / {n} = {c}")