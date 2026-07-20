#Esercizio 1

# 1. Variabile stringa
store_name = "Fresh Market"
print(store_name)

# 2. Variabile numerica
items_in_stock = 42
print(items_in_stock)

# 3. Cambiare valore di una variabile
temperature = 20
print(temperature)
temperature = 35
print(temperature)

# 4. Somma di due variabili numeriche
a = 10
b = 5
print(a + b)

# 5. Variabile booleana
is_open = True
print(is_open)

############################################################################################
#Esercizio 2

# 1. Nome corretto
total_price = 19.99        

# 2. Correggi nome errato
user_name = "Mario"        
print(user_name)

# 3. Rinomina per maggiore chiarezza
x = 25                       
customer_age = x     
del x
print(customer_age)

# 4. Tre variabili in snake_case
product_name = "Pasta"
total_price = 3.50
items_in_cart = 4
print(product_name, total_price, items_in_cart)

# 5. class = 10 non è valido perché "class" è una parola riservata di Python             
school_class = 10         
print(school_class)

############################################################################################
#Esercizio 3

# 1. Stringa con nome prodotto
product_name = "Caffè Arabica"
print(product_name)

# 2. Stringa con virgolette singole
print('Benvenuto nel negozio!')

# 3. Unire due stringhe con +
first_name = "Mario"
last_name = "Rossi"
full_name = first_name + " " + last_name
print(full_name)

# 4. Lunghezza di una stringa con len()
city = "Roma"
print(len(city))

# 5. Frase assegnata a una variabile
welcome_message = "Grazie per il tuo acquisto!"
print(welcome_message)

############################################################################################
#Esercizio 4

# 1. Frase su due righe con \n
print("Prima riga\n" "Seconda riga")

# 2. Tabulazione tra due parole
print("Nome:\t""Mario")

# 3. Frase con virgolette al suo interno
print("Il prodotto si chiama \"Caffè Arabica\"")

# 4. Percorso file con \\
print("C:\\Users\\Mario\\Documenti\\file.txt")

# 5. Frase con \n e \t combinati
print("Ordine ricevuto:\n \tProdotto: Pasta\n \tQuantità: 3\n \tPrezzo: 2.50€")

############################################################################################
#Esercizio 5

# 1. F-string con nome e prezzo
product_name = "Pasta Barilla"
price = 1.99
print(f"Prodotto: {product_name}, Prezzo: {price}€")

# 2. Totale con due variabili numeriche
quantity = 3
unit_price = 2.50
print(f"Totale ordine: {quantity * unit_price}€")

# 3. Frase con valore booleano
in_stock = True
print(f"Prodotto disponibile: {in_stock}")

# 4. F-string con espressione matematica
length = 5
width = 3
print(f"Area del rettangolo: {length * width} cm²")

# 5. Stringa e numerica insieme
customer_name = "Mario"
items = 4
print(f"Ciao {customer_name}, hai {items} articoli nel carrello.")

############################################################################################
#Esercizio 6

# 1. Stringa in maiuscolo
product = "caffè arabica"
print(product.upper())

# 2. Rimuovi spazi con strip()
username = "   Mario Rossi   "
print(username.strip())

# 3. Sostituisci una parola con replace()
phrase = "Buongiorno cliente!"
print(phrase.replace("cliente", "Mario"))

# 4. Posizione di una lettera con index()
city = "Roma"
print(city.index("m"))

# 5. Formato titolo con title()
title = "benvenuto nel negozio fresh market"
print(title.title())

############################################################################################
#Esercizio 7

# 1. Variabile int e float
items = 5               # int — numero intero
price = 2.99            # float — numero decimale
print(items, price)

# 2. Moltiplicazione
length = 6
width = 4
print(f"Area: {length * width}")

# 3. Sottrazione
total = 100.00
discount = 15.50
print(f"Totale scontato: {total - discount}€")

# 4. Tipo di una variabile con type()
quantity = 10
temperature = 36.6
print(type(quantity))
print(type(temperature))

# 5. Risultato di un calcolo assegnato a variabile
unit_price = 3.50
units_sold = 8
total_revenue = unit_price * units_sold
print(f"Guadagno totale: {total_revenue}€")

############################################################################################
#Esercizio 8

# Calcola il resto di una divisione
numero1 = 10
numero2 = 3
resto = numero1 % numero2
print(f"Il resto di {numero1} diviso {numero2} è {resto}")

# Usa l'operatore ** per una potenza
base = 2
esponente = 5
potenza = base ** esponente
print(f"Il risultato di {base} elevato a {esponente} è {potenza}")

# Usa la divisione intera //
numero1 = 10
numero2 = 3
divisione_intera = numero1 // numero2
print(f"Il risultato della divisione intera di {numero1} diviso {numero2} è {divisione_intera}")

# Calcola il totale di un acquisto
prezzo_articolo = 50
quantita = 3
totale_acquisto = prezzo_articolo * quantita
print(f"Il totale dell'acquisto è {totale_acquisto} euro")

# Scrivi un'espressione che usi almeno 3 operatori
espressione = (10 + 5) * 2 - 3
print(f"Il risultato dell'espressione (10 + 5) * 2 - 3 è {espressione}")

############################################################################################
#Esercizio 9

# 1. Converti una stringa numerica in int
stringa_numerica = "123"
numero = int(stringa_numerica)
print(f"La stringa '{stringa_numerica}' convertita in int è {numero}")

# 2. Converti un numero in stringa
numero = 456
stringa = str(numero)
print(f"Il numero {numero} convertito in stringa è '{stringa}'")

# 3. Moltiplica una stringa convertita in numero
stringa_numerica = "5"
numero = int(stringa_numerica)
risultato_moltiplicazione = numero * 2
print(f"La stringa '{stringa_numerica}' convertita in int e moltiplicata per 2 è {risultato_moltiplicazione}")

# 4. Usa input() e converti il valore in int
input_stringa = input("Inserisci un numero: ")  # L'input dell'utente verrà preso come stringa
numero_input = int(input_stringa)
print(f"Il numero inserito convertito in int è {numero_input}")

# 5. Spiega cosa succede se converti "abc" in int
try:
    stringa_non_numerica = "abc"
    numero_non_numerico = int(stringa_non_numerica)
except ValueError:
    print(f"Errore: impossibile convertire '{stringa_non_numerica}' in un numero intero.")