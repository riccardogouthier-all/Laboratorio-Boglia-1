'''
Terzo Esercizio 
1 - Creare una classe Calcolo con un costruttore di default (senza parametri) che consenta di eseguire vari calcoli su numeri interi. 
2 - Creare un metodo chiamato Factorial() che permetta di calcolare il fattoriale di un intero. Testare il metodo istanziando la classe. 
3 - Creare un metodo chiamato Sum() che consenta di calcolare la somma dei primi n interi 1 + 2 + 3 + .. + n. Prova questo metodo. 
4 - Creare un metodo tableMult() che crea e visualizza la tabellina di un dato intero. Quindi creare un metodo allTablesMult() per visualizzare tutte le tabelline di numeri interi 1, 2, 3, ..., 9. 
'''

class Calcolo:
    def __init__(self):
        pass

    '''Fattoriale'''
    def Factorial(self, n):
        if n < 0:
            print("Il fattoriale non è definito per numeri negativi.")
        if n == 0 or n == 1:
            return 1
        risultato = 1
        for i in range(2, n + 1):
            risultato *= i
        return risultato

    '''Somma primi n interi'''
    def Sum(self, n):
        if n < 1:
            print("n deve essere un intero positivo.")
        return sum(range(1, n + 1))

    '''Tabellina di un numero'''
    def tableMult(self, n):
        righe = []
        for i in range(1, 11):
            righe.append(f" {n} x {i:2} = {n * i:3}")
        return righe

    '''Tutte le tabelline da 1 a 9'''
    def allTablesMult(self):
        '''Raccoglie le righe di tutte le tabelline'''
        tabelline = [self.tableMult(n) for n in range(1, 11)]

        '''Stampa riga per riga in orizzontale'''
        for i in range(10):
            print(" // ".join(tabelline[n][i] for n in range(10)))

if __name__ == "__main__":
    '''Test della classe Calcolo'''
    c = Calcolo()
    '''Test Factorial'''
    print("\n","=" * 60)
    print("\nFATTORIALE")
    lista_test_factorial = [0, 1, 5, 10]
    for n in lista_test_factorial:
        print(f" {n}! = {c.Factorial(n)}")
    '''Test Sum'''
    print("\n","=" * 60)
    print("\nSOMMA PRIMI N INTERI")
    lista_test_sum = [5, 10, 100]
    for n in lista_test_sum:
        print(f" Somma dei numeri da 1 a {n} = {c.Sum(n)}")
    '''Test tableMult'''
    print("\n","=" * 60)
    print("\nTABELLINA SINGOLA")
    for riga in c.tableMult(7):
        print(riga)
    '''Test allTablesMult'''
    print("\n","=" * 60)
    print("\nTUTTE LE TABELLINE")
    c.allTablesMult()
    print("\n","=" * 60, "\n")