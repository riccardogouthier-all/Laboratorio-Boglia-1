
ESCLUSE = (".tmp", ".log")

nome = input("Inserisci il tuo nome: ")

inclusi = []
esclusi = []

print("Inserisci i nomi dei file (scrivi STOP per terminare):")

while True:
    file = input().strip()
    if file.upper() == "STOP":
        break
    if file.endswith(ESCLUSE):
        esclusi.append(file)
    else:
        inclusi.append(file)

print(f"\nBackup Report - {nome}")
print(f"File inclusi: {len(inclusi)}")
print(f"File esclusi: {len(esclusi)}")
print("Elenco inclusi:")
for f in inclusi:
    print(f"- {f}")
print("Elenco esclusi:")
for f in esclusi:
    print(f"- {f}")