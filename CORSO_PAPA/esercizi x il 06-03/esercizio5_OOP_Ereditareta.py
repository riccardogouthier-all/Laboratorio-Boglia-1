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
        self.__operando1 = operando1
        self.__operando2 = operando2

    def __str__(self):
        return f"AritmeticaDue(operando1={self.__operando1}, operando2={self.__operando2})"

    @property
    def differenza(self):
        return self.__operando1 - self.__operando2

    @property
    def prodotto(self):
        return self.__operando1 * self.__operando2

    @property
    def confronto_prodotto(self, altro):
        return self.prodotto() > altro.prodotto()

class AritmeticaTre(AritmeticaDue):
    def __init__(self, operando3)
        super().__init__(operando1, operando2)
        self.__operando3 = operando3

    @property
    def 



