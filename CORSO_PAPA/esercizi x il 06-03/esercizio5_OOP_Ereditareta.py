'''
Creare una classe AritmeticaDue con attributi operando1 e operando2. 
Definire il costruttore utilizzando parametri con valori predefiniti e il metodo str. 
Aggiungere due metodi uno che restituisca la differenza e l'altro il prodotto dei due operandi. 
Implementare un terzo metodo che permetta il confronto tra il risultato del prodotto di due oggetti AritmeticaDue 
(in sostanza indicare se il prodotto è maggiore di quello calcolato nell'oggetto AritmeticaDue passato come parametro). 
Derivare dalla classe AritmeticaDue la classe AritmeticaTre aggiungendo l'attributo operando3. 
Ridefinire il costruttore, il metodo str e i tre metodi differenza, prodotto e confronto. 
Aggiungere un metodo per il calcolo della somma di tutti gli attributi. 
Provare le classi e i metodi implementati. 
'''

class AritmeticaDue:
    def __init__(self, operando1=0, operando2=0):
        self._operando1 = operando1
        self._operando2 = operando2

    def __str__(self):
        return f"AritmeticaDue(operando1= {self._operando1:3}, operando2= {self._operando2:3})"

    def differenza(self):
        return self._operando1 - self._operando2

    def prodotto(self):
        return self._operando1 * self._operando2

    def confronto_prodotto(self, altro):
        if not isinstance(altro, AritmeticaDue):
            raise TypeError("Il parametro deve essere un'istanza di AritmeticaDue")
        if self.prodotto() > altro.prodotto():
            return f"{self.prodotto()} > {altro.prodotto()}"
        elif self.prodotto() < altro.prodotto():
            return f"{self.prodotto()} < {altro.prodotto()}"
        else:
            return f"{self.prodotto()} = {altro.prodotto()}"

class AritmeticaTre(AritmeticaDue):
    def __init__(self, operando1, operando2, operando3):
        super().__init__(operando1, operando2)
        self._operando3 = operando3

    def somma(self):
        return self._operando1 + self._operando2 + self._operando3

    def __str__(self):
        return f"AritmeticaTre(operando1= {self._operando1:3}, operando2= {self._operando2:3}, operando3= {self._operando3:3})"
    
    def differenza(self):
        return self._operando1 - self._operando2 - self._operando3
    
    def prodotto(self):
        return self._operando1 * self._operando2 * self._operando3
    
    def confronto_prodotto(self, altro):
        if not isinstance(altro, AritmeticaDue):
            raise TypeError("Il parametro deve essere un'istanza di AritmeticaDue")
        if self.prodotto() > altro.prodotto():
            return f"{self.prodotto()} > {altro.prodotto()}"
        elif self.prodotto() < altro.prodotto():
            return f"{self.prodotto()} < {altro.prodotto()}"
        else:
            return f"{self.prodotto()} = {altro.prodotto()}"

# Prove
print("\n","=" * 100,"\n")

a = AritmeticaDue(5, 3)
b = AritmeticaDue(10, 3)
c = AritmeticaDue(5, 10)
print(a)
print(b)
print(c,"\n")
print("Differenza:", a.differenza())
print("Prodotto:", a.prodotto())
print("Confronto prodotto a vs b:", a.confronto_prodotto(b))

print("\n","=" * 100,"\n")

x = AritmeticaTre(6, 4, 2)
y = AritmeticaTre(2, 4, 6)
z = AritmeticaTre(10, 5, 1)
print(x)
print(y)
print(z,"\n")
print("Differenza:", x.differenza())
print("Prodotto:", x.prodotto())
print("Somma:", x.somma())
print("Confronto prodotto x vs z:", x.confronto_prodotto(z))

print("\n","=" * 100,"\n")