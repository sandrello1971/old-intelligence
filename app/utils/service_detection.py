import re

# Sinonimi / parole chiave per ogni servizio
KEYWORDS = {
    "Cashback": ["cashback"],
    "Know How": ["know how", "know-how"],
    "Bandi": ["bandi", "bando", "contributo"],
    "Finanziamenti": ["finanziamenti", "finanziamento", "credito"],
    "Incarico 24 mesi": ["incarico 24 mesi", "durata 24 mesi"],
    "Patent Box": ["patent box", "agevolazione brevetti"],
    "Collaborazione": ["collaborazione", "partner", "sinergia"],
    "Formazione 4.0": ["formazione 4.0", "formazione", "4.0"],
    "Generico": ["generico", "generale", "varie"],
    "Transizione 5.0": ["transizione 5.0", "5.0", "transizione"],
    "Altro": ["altro", "non specificato"]
}

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'[^a-z0-9àèéìòù ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_services_from_description(description: str) -> list[str]:
    desc = normalize(description)
    found = []

    for service, synonyms in KEYWORDS.items():
        for kw in synonyms:
            if kw in desc:
                found.append(service)
                break

    return found
