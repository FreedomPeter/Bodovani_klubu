import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

BASE_URL = "https://online.atletika.cz/clenska-sekce/oddily/adresar-oddilu/?strana="

clubs = []


def infer_region_from_address(address: str) -> str:
    if not address:
        return "Neznámý"

    text = " ".join(address.split())

    # First try PSČ prefix because it is the most reliable signal in this dataset.
    m = re.search(r"PSČ\s*(\d{3})\s*\d{2}", text)
    if m:
        prefix = int(m.group(1))

        if 100 <= prefix <= 199:
            return "Pražský"
        if 250 <= prefix <= 299:
            return "Středočeský"
        if 370 <= prefix <= 399:
            return "Jihočeský"
        if 300 <= prefix <= 349:
            return "Plzeňský"
        if 350 <= prefix <= 364:
            return "Karlovarský"
        if 400 <= prefix <= 441:
            return "Ústecký"
        if 460 <= prefix <= 473 or 500 <= prefix <= 514:
            return "Liberecký"
        if 516 <= prefix <= 551:
            return "Královéhradecký"
        if 530 <= prefix <= 572:
            return "Pardubický"
        if 580 <= prefix <= 594 or 670 <= prefix <= 676:
            return "Vysočina"
        if 600 <= prefix <= 619 or 664 <= prefix <= 693:
            return "Jihomoravský"
        if 760 <= prefix <= 769 or 686 <= prefix <= 688:
            return "Zlínský"
        if 779 <= prefix <= 789 or 750 <= prefix <= 753:
            return "Olomoucký"
        if 700 <= prefix <= 749 or 792 <= prefix <= 794:
            return "Moravskoslezský"

    # Fallback by city / address text for rows where PSČ is malformed or missing.
    fallback_keywords = {
        "Pražský": ["Praha", "Kbely", "Uhříněves", "Hostivař", "Stodůlky", "Radotín", "Smíchov", "Vinohrady", "Letňany"],
        "Středočeský": ["Kladno", "Kolín", "Nymburk", "Příbram", "Beroun", "Benešov", "Čelákovice", "Neratovice", "Mladá Boleslav", "Vlašim", "Poděbrady", "Rakovník", "Říčany", "Roztoky", "Slaný", "Brandýs", "Milovice", "Kutná Hora"],
        "Jihočeský": ["České Budějovice", "Tábor", "Písek", "Prachatice", "Strakonice", "Třeboň", "Milevsko", "Jindřichův Hradec", "Sezimovo Ústí", "Trhové Sviny", "Veselí nad Lužnicí", "Bechyně"],
        "Plzeňský": ["Plzeň", "Domažlice", "Klatovy", "Tachov", "Stříbro", "Nýřany", "Přeštice", "Rokycany", "Sušice", "Horšovský Týn"],
        "Karlovarský": ["Karlovy Vary", "Cheb", "Sokolov", "Ostrov", "Kraslice", "Mariánské Lázně", "Chodov"],
        "Ústecký": ["Ústí nad Labem", "Teplice", "Most", "Louny", "Chomutov", "Bílina", "Krupka", "Rumburk", "Děčín", "Litvínov", "Lovosice", "Varnsdorf", "Žatec", "Kadaň", "Klášterec nad Ohří", "Duchcov", "Štětí", "Počerady"],
        "Liberecký": ["Liberec", "Jablonec", "Česká Lípa", "Turnov", "Semily", "Nový Bor", "Cvikov", "Desná", "Jilemnice", "Lomnice nad Popelkou", "Jičín"],
        "Královéhradecký": ["Hradec Králové", "Trutnov", "Dvůr Králové", "Jaroměř", "Náchod", "Nové Město nad Metují", "Dobruška", "Vrchlabí", "Úpice", "Ostroměř", "Jičín", "Hajnice"],
        "Pardubický": ["Pardubice", "Chrudim", "Svitavy", "Litomyšl", "Lanškroun", "Polička", "Choceň", "Vysoké Mýto", "Česká Třebová", "Ústí nad Orlicí", "Žamberk", "Slatiňany", "Týniště nad Orlicí", "Dlouhá Třebová", "Jablonné nad Orlicí", "Kunvald", "Klášterec nad Orlicí"],
        "Vysočina": ["Jihlava", "Třebíč", "Žďár nad Sázavou", "Havlíčkův Brod", "Pelhřimov", "Humpolec", "Pacov", "Ledeč nad Sázavou", "Světlá nad Sázavou", "Velké Meziříčí", "Nové Město na Moravě", "Moravské Budějovice", "Okříšky", "Jaroměřice nad Rokytnou", "Jemnice"],
        "Jihomoravský": ["Brno", "Blansko", "Břeclav", "Vyškov", "Hodonín", "Znojmo", "Kyjov", "Kuřim", "Rosice", "Mikulčice", "Tišnov", "Židlochovice", "Hustopeče", "Valtice", "Letovice", "Moravský Krumlov", "Slavkov u Brna", "Klobouky u Brna"],
        "Zlínský": ["Zlín", "Uherské Hradiště", "Uherský Brod", "Kroměříž", "Otrokovice", "Holešov", "Valašské Meziříčí", "Vsetín", "Hulín", "Hluk", "Rožnov pod Radhoštěm", "Chropyně"],
        "Olomoucký": ["Olomouc", "Prostějov", "Přerov", "Šumperk", "Šternberk", "Uničov", "Zábřeh", "Hranice"],
        "Moravskoslezský": ["Ostrava", "Opava", "Karviná", "Havířov", "Bohumín", "Třinec", "Nový Jičín", "Kopřivnice", "Orlová", "Frýdek-Místek", "Krnov", "Poruba", "Rýmařov", "Bruntál", "Ludgeřovice", "Bolatice", "Kobeřice", "Razová", "Hošťálkovice"],
    }

    lowered = text.lower()
    for region, keywords in fallback_keywords.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                return region

    return "Neznámý"


for page in range(1, 20):
    url = BASE_URL + str(page)

    print("loading page", page)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")

    if not rows:
        break

    for row in rows:
        td = row.find_all("td")

        if len(td) < 5:
            continue

        adresa = td[4].text.strip()

        club = {
            "zkratka": td[1].text.strip(),
            "nazev": td[2].text.strip(),
            "kontakt": td[3].text.strip() if len(td) > 3 else "",
            "adresa": adresa,
            "kraj": infer_region_from_address(adresa),
        }

        clubs.append(club)

    time.sleep(0.5)

# Deduplicate by abbreviation + club name because the source sometimes repeats rows.
df = pd.DataFrame(clubs).drop_duplicates(subset=["zkratka", "nazev"]).reset_index(drop=True)

# Put kraj earlier so the output is easier to use in the app.
df = df[["zkratka", "nazev", "kraj", "kontakt", "adresa"]]


df.to_csv("clubs_database.csv", index=False)
df.to_json("clubs_database.json", orient="records", force_ascii=False)

print("Hotovo.")
print("Počet klubů:", len(df))
print(df.head(10).to_string(index=False))