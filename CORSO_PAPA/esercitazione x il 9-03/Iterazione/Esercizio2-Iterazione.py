'''
Autore: Riccardo Gouthier
Data: 08/03/2026
Titolo: Si hanno in input N saldi di conti correnti bancari. Si vuole in output la media aritmetica dei
soli conti correnti che hanno un saldo negativo.
'''

# Inizializzazioni variabili
lista = []
k = 0
media = 0.0
n = 0
somma_conti = 0.0
conti_negativi = []
y = 0

# Sezione di input Dati
while y == 0:
    try:
        lista = []
        
        while k == 0:
            num = float(input(f"inserisci il saldo del conto bancario n: {len(lista) + 1}: \n"))
            lista.append(num)
            scelta = input("vuoi inserire altri conti? y/n \n")
            if scelta.lower() == 'n':
                    k = 1
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
for i in range(len(lista)):
    if lista[i] < 0:
           somma_conti += lista[i]
           n += 1
           conti_negativi.append(lista[i])

# Eventuali sotto processi di Elaborazione
if n != 0:
    media = somma_conti / n

# Sezione di output
print(f"La media dei conti negativi e': {media} perche la media di {conti_negativi} / {n} = {media}")