
class Calcolo:
    def __init__(self):
        pass

    '''Tabellina di un numero'''
    def tableMult(self, n):
        righe = []
        for i in range(1, 11):
            righe.append(f" {n} x {i:2} ={n * i:3}")
        return righe

    def allTablesMult(self):
        '''Raccoglie le righe di tutte le tabelline'''
        tabelline = [self.tableMult(n) for n in range(1, 11)]
        
        '''Stampa riga per riga in orizzontale'''
        for i in range(10):
            print(" // ".join(tabelline[n][i] for n in range(10)))



if __name__ == "__main__":

    
    c = Calcolo()
    
    '''Test tableMult'''
    print("\nTABELLINA SINGOLA")
    for riga in c.tableMult(7):
        print(riga)
    
    '''Test allTablesMult'''
    print("\nTUTTE LE TABELLINE")
    c.allTablesMult()


print(f"TEST CLASSE ARITMETICA DUE E ARITMETICA TRE") 
print(f'''
TEST CLASSE ARITMETICA DUE E ARITMETICA TRE''')