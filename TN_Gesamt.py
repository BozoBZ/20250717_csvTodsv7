import re
from datetime import datetime

input_file = 'CoppaReg_Indiv.csv'
output_file = 'CoppaReg_Indiv.DSV7'

# === Funzione tempo robusta ===
def normalizza_tempo(raw):
    raw = raw.replace("'", ":").replace(" ", "").replace(".", ",")
    if ':' not in raw:
        return f"00:00:{raw}"
    parts = raw.split(":")
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1]}"
    elif len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2]}"
    return "00:00:00,00"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

# === Estrai intestazione evento ===
evento_nome = lines[0]
info = lines[1]
vasca_len = re.search(r'V\.\s*(\d{2})m', info).group(1) if re.search(r'V\.\s*\d{2}m', info) else '50'
piscina_nome = re.search(r'Piscina\s+.+?-', info)
piscina_nome = piscina_nome.group(0).strip('- ').strip() if piscina_nome else 'Piscina Comunale'

# === Gestione ABSCHNITT
abschnitt_map = {}
abschnitt_lines = []
abschnitt_counter = 1
for line in lines:
    match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
    if match:
        date_txt = match.group(1)
        if date_txt not in abschnitt_map:
            abschnitt_map[date_txt] = abschnitt_counter
            date_iso = datetime.strptime(date_txt, "%d/%m/%Y").strftime("%Y-%m-%d")
            abschnitt_lines.append(f"ABSCHNITT: {abschnitt_counter};{date_iso};08:30;;")
            abschnitt_counter += 1

# === Intestazione output
output = [
    "(* erzeugt mit Darios' Python - DAS Schwimmwettkampfprogramm *)",
    "(* Version 1.0 vom 24.07.2025                       *)",
    "FORMAT: Wettkampfergebnisliste;7;",
    "ERZEUGER: Dario's PY;1.00;dtaraboi67@gmail.com;",
    f"VERANSTALTUNG: {evento_nome};{piscina_nome};{vasca_len};AUTOMATISCH;",
    f"VERANSTALTUNGSORT: {piscina_nome};Via Vasca 1;39012;Rovereto;ITA;;;;"
]
output.extend(abschnitt_lines)

# === Inizializzazioni
verein_lines = []
wettkampf_lines = []
pnergebnis_lines = []

club_ids = {}
next_club_id = 1001
wertung_map = {}
wertung_counter = 1001
athlete_registry = {}
athlete_id_counter = 1
wk_counter = 1
platz_counter = 1
style_map = {
    'Stile Libero': 'F',
    'S. Libero': 'F',
    'Farfalla': 'S',
    'Dorso': 'R',
    'Rana': 'B',
    'Misti': 'L',
    'SL': 'F',
    'FA': 'S',
    'DO': 'R',
    'RA': 'B',
    'MI': 'L',
}

current_abschnitt = 1
gender_code = ''
current_wertung = ''
wk_id = 0

for line in lines[2:]:
    match_date = re.search(r'(\d{2}/\d{2}/\d{4})', line)
    if match_date:
        date_txt = match_date.group(1)
        current_abschnitt = abschnitt_map.get(date_txt, current_abschnitt)

    match_gara = re.match(r"(\d{2,4})\s+([A-Za-zàèéìòùA-Z.']+)\s*-\s*([A-Za-z0-9 ]+)\s+(Maschili|Femminili)", line)
    if match_gara:
        distanza, stile_nome, categoria, genere = match_gara.groups()
        gender_code = 'M' if genere.lower().startswith('masch') else 'W'
        stile_code = style_map.get(stile_nome.strip(), 'F')
        wertung_key = f"{categoria.strip()} {gender_code}"
        if wertung_key not in wertung_map:
            wertung_map[wertung_key] = wertung_counter
            wertung_counter += 1
        current_wertung = wertung_map[wertung_key]
        nome_commento = f"{distanza}m {stile_nome.strip()} {gender_code}"
        wk_id = wk_counter
        wettkampf_lines.append(
            f"WETTKAMPF: {wk_counter};E;{current_abschnitt};1;{distanza};{stile_code};GL;{gender_code};SW;;; (* {nome_commento} *)"
        )
        platz_counter = 1
        wk_counter += 1
        continue

    match_atleta = re.match(r"\d+\s+(.+?)\s+(\d{4})\s+(\w+)\s+(.+?)\s+\d+\s+\d+\s+\d+\.?\s+([\d:'\.]+)", line)
    if match_atleta:
        raw_name, birth, nation, club, tempo_raw = match_atleta.groups()
        tokens = raw_name.strip().split()
        cognome = tokens[0].upper()
        nome_fmt = " ".join(n.capitalize() for n in tokens[1:])
        full_name = f"{cognome}, {nome_fmt}"

        if full_name not in athlete_registry:
            athlete_code = f"A{athlete_id_counter:06d}"
            athlete_registry[full_name] = (athlete_id_counter, athlete_code)
            athlete_id_counter += 1
        athlete_id, athlete_code = athlete_registry[full_name]

        tempo = normalizza_tempo(tempo_raw)

        if club not in club_ids:
            club_ids[club] = next_club_id
            verein_lines.append(f"VEREIN: {club};{next_club_id};17;ITA;")
            next_club_id += 1
        club_id = club_ids[club]

        # Ensure wertung_key is always defined for each athlete
        try:
            wertung_key_str = wertung_key
        except NameError:
            wertung_key_str = str(current_wertung)

        pnergebnis_lines.append(
            f"PNERGEBNIS: {wk_id};E;{current_wertung};{platz_counter};;{full_name};{athlete_code};{athlete_id};{gender_code};{birth};;{club};{club_id};{tempo};;;{nation};;; (* {wertung_key_str} *)"
        )
        platz_counter += 1

output.extend(verein_lines)
output.append('')
output.extend(wettkampf_lines)
output.append('')
output.extend(pnergebnis_lines)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("✅ File ROVERETO_Complete.DSV7 generato con nomi e ID atleta corretti")
print(f"✅ Totale tempi esportati: {len(pnergebnis_lines)}")
print(f"✅ Totale gare esportate: {len(wettkampf_lines)}")