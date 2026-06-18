"""
logica_algoritmi.py — Sezione 1: LOGICA & ALGORITMI

Contiene le funzioni per:
    - calcolo media personale e voto finale (anche pesato, se configurato)
    - assegnazione debiti formativi per materia
    - promozione/bocciatura con regole personalizzabili
    - raggruppamento per fasce di rendimento
    - ordinamento (bubble sort, quick sort) applicato agli studenti

Tutte le funzioni che "arricchiscono" lo studente (media, debiti, esito)
lavorano in place sui dizionari della lista passata, cosi' da poterle
concatenare liberamente nella pipeline, nello stesso ordine in cui sono
definite qui sotto (media -> debiti -> esito).
"""

# import librerire standard
import statistics
import math

def calcola_media_e_voto_finale(studenti: list[dict], config: dict) -> None:       # STEP 11 - Calcolo media e voto finale - lavora in place, non ritorna nulla
    """Calcola la media personale di ogni studente e il voto finale (intero,
    arrotondato). Se config contiene 'pesi_materie' (es. {"Matematica": 2}),
    la media viene calcolata come media pesata, altrimenti come media semplice."""
    pesi = config.get("pesi_materie")          # opzionale: dizionario materia -> peso

    for studente in studenti:
        voti = studente["voti"]

        if not voti:
            studente["media_personale"] = 0.0
            studente["voto_finale"] = 0
            continue

        if pesi:
            totale_pesato = sum(voto * pesi.get(materia, 1) for materia, voto in voti.items())
            totale_pesi = sum(pesi.get(materia, 1) for materia in voti)
            media = totale_pesato / totale_pesi
        else:
            media = statistics.mean(voti.values())

        studente["media_personale"] = math.floor(media + 0.5, 2)          # arrotondamento standard a due decimali
        studente["voto_finale"] = math.floor(media + 0.5)          # arrotondamento con math perchè round() arrotonda all'intero pari più vicino

    print(f"[Step 11] Media e voto finale calcolati per {len(studenti)} studenti.")


def assegna_debiti_formativi(studenti: list[dict], config: dict) -> None:       # STEP 12 - Assegnazione debiti formativi - lavora in place, non ritorna nulla
    """
    Individua per ogni studente le materie con voto insufficiente (sotto la
    soglia configurata in 'soglia_debito', default 6) e le salva in 'debiti'.
    """
    soglia = config.get("soglia_debito", 6)

    for studente in studenti:
        studente["debiti"] = [materia for materia, voto in studente["voti"].items() if voto < soglia]

    n_con_debiti = sum(1 for s in studenti if s["debiti"])
    print(f"[Step 12] Debiti formativi assegnati (soglia: {soglia}). Studenti con almeno un debito: {n_con_debiti}.")


def determina_esito(studenti: list[dict], config: dict) -> None:       # STEP 13 - Promozione/bocciatura - lavora in place, non ritorna nulla
    """
    Determina l'esito di ogni studente (Promosso/Bocciato) in base a regole
    personalizzabili da config: media minima ('media_minima_promozione', default 6),
    numero massimo di debiti tollerati ('debiti_max_tollerati', default 2) e
    assenze massime consentite ('assenze_max_consentite', default 25).
    Richiede che siano già state calcolate 'media_personale' e 'debiti'.
    """
    media_minima = config.get("media_minima_promozione", 6)
    debiti_max = config.get("debiti_max_tollerati", 2)
    assenze_max = config.get("assenze_max_consentite", 25)

    for studente in studenti:
        motivi = []

        if studente["media_personale"] < media_minima:
            motivi.append(f"media personale {studente['media_personale']} sotto la soglia {media_minima}")

        n_debiti = len(studente.get("debiti", []))
        if n_debiti > debiti_max:
            motivi.append(f"{n_debiti} debiti formativi (max tollerati: {debiti_max})")

        if studente["assenze"] > assenze_max:
            motivi.append(f"{studente['assenze']} assenze (max consentite: {assenze_max})")

        studente["esito"] = "Bocciato" if motivi else "Promosso"
        studente["motivi_esito"] = motivi

    n_promossi = sum(1 for s in studenti if s["esito"] == "Promosso")
    print(f"[Step 13] Esiti determinati: {n_promossi} promossi, {len(studenti) - n_promossi} bocciati.")


def raggruppa_per_fascia_rendimento(studenti: list[dict], config: dict) -> dict[str, list[dict]]:       # STEP 14 - Raggruppamento per fasce di rendimento - ritorna dizionario {fascia: lista studenti}
    """Raggruppa gli studenti in fasce di rendimento in base alla media personale.
    Le fasce sono definite in config['fasce_rendimento'] come lista [nome, soglia_minima],
    ordinate dalla più alta alla più bassa. Richiede 'media_personale' già calcolata."""
    fasce_config = config.get("fasce_rendimento", [
        ["Eccellente", 9],
        ["Buono", 7],
        ["Sufficiente", 6],
        ["Insufficiente", 0],
    ])

    fasce = {nome: [] for nome, _ in fasce_config}

    for studente in studenti:
        for nome, soglia_minima in fasce_config:
            if studente["media_personale"] >= soglia_minima:
                fasce[nome].append(studente)
                break

    print("[Step 14] Studenti raggruppati per fascia di rendimento:")
    for nome, lista in fasce.items():
        print(f"           {nome}: {len(lista)} studenti")

    return fasce       # dizionario {fascia: lista studenti}


def bubble_sort_studenti(studenti: list[dict], chiave: str, decrescente: bool = True) -> list[dict]:       # STEP 15 - Ordinamento bubble sort - ritorna nuova lista ordinata
    """Ordina gli studenti con l'algoritmo bubble sort, confrontando il valore
    associato a 'chiave' (es. 'media_personale', 'assenze', 'cognome').
    Non modifica la lista originale."""
    lista = studenti.copy()
    n = len(lista)
    passaggi = 0

    for i in range(n - 1):
        scambiato = False
        for j in range(n - 1 - i):
            if decrescente:
                condizione = lista[j][chiave] < lista[j + 1][chiave]
            else:
                condizione = lista[j][chiave] > lista[j + 1][chiave]

            if condizione:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
                scambiato = True

        passaggi += 1
        if not scambiato:        # ottimizzazione: se non ci sono stati scambi la lista è già ordinata
            break

    print(f"[Step 15] Bubble sort completato su '{chiave}' ({n} studenti, {passaggi} passaggi).")
    return lista       # nuova lista ordinata


def quick_sort_studenti(studenti: list[dict], chiave: str, decrescente: bool = True) -> list[dict]:       # STEP 16 - Ordinamento quick sort - ritorna nuova lista ordinata
    """Ordina gli studenti con l'algoritmo quick sort (ricorsivo, pivot centrale),
    confrontando il valore associato a 'chiave'. Non modifica la lista originale."""

    def _quick_sort(lista: list[dict]) -> list[dict]:
        if len(lista) <= 1:
            return lista

        pivot = lista[len(lista) // 2][chiave]

        if decrescente:
            prima  = [s for s in lista if s[chiave] > pivot]
            uguali = [s for s in lista if s[chiave] == pivot]
            dopo   = [s for s in lista if s[chiave] < pivot]
        else:
            prima  = [s for s in lista if s[chiave] < pivot]
            uguali = [s for s in lista if s[chiave] == pivot]
            dopo   = [s for s in lista if s[chiave] > pivot]

        return _quick_sort(prima) + uguali + _quick_sort(dopo)

    risultato = _quick_sort(studenti)
    print(f"[Step 16] Quick sort completato su '{chiave}' ({len(studenti)} studenti).")
    return risultato       # nuova lista ordinata