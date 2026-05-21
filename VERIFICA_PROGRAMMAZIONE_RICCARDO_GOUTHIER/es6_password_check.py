
nome = input("Inserisci il tuo nome: ").strip()
password = input("Inserisci la password: ").strip()

lunghezza_ok = len(password) >= 8
ha_maiuscola = any(c.isupper() for c in password)
ha_minuscola = any(c.islower() for c in password)
ha_numero = any(c.isdigit() for c in password)

if lunghezza_ok and ha_maiuscola and ha_minuscola and ha_numero:
    print(f"{nome} - Password valida")
else:
    print(f"{nome} - Password non valida")