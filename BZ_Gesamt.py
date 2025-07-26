import re
from datetime import datetime

# === CARICA CSV ===
with open("BZ_Completo_Pulito.csv", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# === Estrai DATI MANIFESTAZIONE dalle prime 2 righe ===
nome_evento = lines[0]
match_info = re.search(r'(.+?)\s+\((\d{2}/\d{2}/\d{4})\)', lines[1])
luogo = match_info.group(1).strip() if match_info else "Luogo Sconosciuto"
data_str = match_info.group(2)
data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")

# === HEADER Wettkampfdefinitionsliste (stile Berlin) ===
wettkopf_lines = [
    '(* generato con Copilot per Dario *)',
    'FORMAT: Wettkampfdefinitionsliste;7;',
    'ERZEUGER: Copilot;1.0;copilot@microsoft.com;',
    f'VERANSTALTUNG: {nome_evento};{luogo};50;AUTOMATISCH;',
    f'VERANSTALTUNGSORT: Lido {luogo};Via Lido 1;39012;{luogo};ITA;;;;',
    'AUSSCHREIBUNGIMNETZ: ;',
    'VERANSTALTER: FIN Alto Adige;',
    'AUSRICHTER: BZ Nuoto;Delladio, Patrick;;;;ITA;;;info@bznuoto.it;',
    f'MELDEADRESSE: Patrick Delladio;Via Lido 1;39012;{luogo};;0471123456;;info@bznuoto.it;',
    'MELDESCHLUSS: 09.07.2025;23:59;',
    'BANKVERBINDUNG: Banca Nuoto;IT60X0542811101000000123456;BNDTIT21;',
    f'ABSCHNITT: 1;{data_iso};07:30;08:30;09:00;;',
    ''
]

# === HEADER Vereinsergebnisliste ===
verein_lines = [
    '[Header]',
    'VERSION=DSV7',
    'LISTE=Vereinsergebnisliste',
    'ERZEUGT=2025-07-17',
    f'VERANSTALTUNG={nome_evento}',
    f'ORT={luogo}',
    f'DATUM={data_iso}',
    ''
]

# === ESTRAI GARE E RISULTATI ===
club_blocks = {}
wk_counter = 1
current_event = ""
gender_code = ""
wertung_counter = 1

for line in lines[2:]:
    match_gara = re.match(r'Gara n\.(\d+) - (.+?) - (.+)', line)
    if match_gara:
        numero, nome, sesso_descr = match_gara.group(1), match_gara.group(2).strip(), match_gara.group(3).lower()
        gender_code = 'M' if 'maschili' in sesso_descr else 'W'
        stile_map = {'Stile Libero': 'F', 'Dorso': 'R', 'Rana': 'B', 'Farfalla': 'S', 'Misti': 'L'}
        abbrev_stile = next((v for k, v in stile_map.items() if k in nome), 'F')
        distanza = re.search(r'(\d{2,4})', nome).group(1)
        descrizione = f"{distanza}m {nome} {sesso_descr}"
        wettkopf_lines.append(f'WETTKAMPF: {wk_counter};E;1;1;{distanza};{abbrev_stile};GL;{gender_code};ITA;;; (* {descrizione} *)')
        wettkopf_lines.append(f'WERTUNG: {wertung_counter};E;{1000+wk_counter};JG;2008;2015;{gender_code};Allievi {gender_code}')
        wettkopf_lines.append(f'MELDEGELD: Wkmeldegeld;0,00;{wk_counter}')
        current_event = f"{numero}. {nome} - {gender_code}"
        wk_counter += 1
        wertung_counter += 1
        continue

    match_atleta = re.match(r'(\d+)\.\s+(.+?)\s+\((\d{4})\)\s+-\s+(.+?)\s+([0-9:.]+)\s+(\d+)', line)
    if match_atleta:
        pos, nome, anno, club, tempo, piazzamento = [match_atleta.group(i).strip() for i in range(1, 7)]
        tempo = tempo.replace(',', '.')
        block = (
            f"[Verein]\n"
            f"NAME={club}\n\n"
            f"[Ergebnis]\n"
            f"SCHWIMMER={nome}\n"
            f"GEBURTSJAHR={anno}\n"
            f"GESCHLECHT={gender_code}\n"
            f"STRECKE={current_event}\n"
            f"ZEIT={tempo}\n"
            f"PLATZ={piazzamento}\n\n"
        )
        club_blocks.setdefault(club, []).append(block)

# === SCRIVI FILE .DSV7 ===
with open("Merano-Wettkampfdefinitionsliste.DSV7", "w", encoding="utf-8") as f:
    f.write('\n'.join(wettkopf_lines))

for club in club_blocks:
    verein_lines.extend(club_blocks[club])

with open("Merano-Vereinsergebnisliste.DSV7", "w", encoding="utf-8") as f:
    f.write('\n'.join(verein_lines))

print("✅ Conversione completata: struttura EasyWK estratta direttamente dal CSV!")
