# Esercizio 1 — Controllo ingresso
age = input()
if age >= 18:
    print("Allowed")

# Esercizio 2 — Sconto su prodotto
price = input()
in_stock = True
if price < 10 and in_stock:
    print("Sconto applicato")

# Esercizio 3 — Accesso con genitore
age = input()
with_parent = bool(input())
if age >= 16 or with_parent:
    print("Accesso consentito")

# Esercizio 4 — Verifica licenza
license_expired = bool(input())
if not license_expired:
    print("Licenza valida")

# Esercizio 5 — Perimetro di sicurezza
sensor_active = bool(input())
movement_detected = bool(input())
if sensor_active and movement_detected:
    print("⚠️ Warning: movimento rilevato!")