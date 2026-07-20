# es3_log_parser.py
# Analizzatore di file access_log.txt
# Formato righe: DATA ORA IP METODO URL STATUS CODE_MS

STUDENTE = input("Inserisci il tuo nome: ")  # <-- Modifica con il tuo nome

def analizza_log(nome_file):
    totale_richieste = 0
    status_200 = 0
    status_404 = 0
    ip_contatore = {}
    somma_ms = 0

    try:
        with open(nome_file, "r") as f:
            for riga in f:
                riga = riga.strip()
                if not riga:
                    continue

                parti = riga.split()

                if len(parti) != 7:
                    continue

                data, ora, ip, metodo, url, status, code_ms = parti

                if not status.isdigit() or not code_ms.isdigit():
                    continue

                status = int(status)
                code_ms = int(code_ms)

                totale_richieste += 1
                somma_ms += code_ms

                if status == 200:
                    status_200 += 1
                elif status == 404:
                    status_404 += 1

                ip_contatore[ip] = ip_contatore.get(ip, 0) + 1

    except FileNotFoundError:
        print(f"Errore: file '{nome_file}' non trovato.")
        return

    if ip_contatore:
        ip_piu_attivo = max(ip_contatore, key=lambda k: ip_contatore[k])
    else:
        ip_piu_attivo = "N/D"

    if totale_richieste > 0:
        tempo_medio = somma_ms / totale_richieste
    else:
        tempo_medio = 0.0

    print(f"Report log - Studente: {STUDENTE}")
    print(f"Totale richieste: {totale_richieste}")
    print(f"Status 200: {status_200}")
    print(f"Status 404: {status_404}")
    print(f"IP più attivo: {ip_piu_attivo}")
    print(f"Tempo medio risposta: {tempo_medio:.2f} ms")

if __name__ == "__main__":
    analizza_log("access_log.txt")