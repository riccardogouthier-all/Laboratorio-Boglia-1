
nome = input("Inserisci il tuo nome: ").strip()
p = input("Inserisci la p: ").strip()

lunghezza_ok = len(p) >= 8
ha_maiuscola = any(c.isupper() for c in p)
ha_minuscola = any(c.islower() for c in p)
ha_numero = any(c.isdigit() for c in p)

if lunghezza_ok and ha_maiuscola and ha_minuscola and ha_numero:
    print(f"{nome} - p valida")
else:
    print(f"{nome} - p non valida")