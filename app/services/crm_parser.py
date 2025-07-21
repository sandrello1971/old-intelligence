def extract_opportunities_from_description(description: str, services: list[str] = None):
    """
    Estrae codici opportunità dalla descrizione e/o lista servizi.
    Ora usa il database dinamicamente invece del mapping hardcoded.
    """
    from app.core.database import SessionLocal
    from app.models.sub_type import SubType
    
    # Get dynamic mapping from database
    db = SessionLocal()
    try:
        # Recupera tutti i servizi con codice dal database
        db_services = db.query(SubType).filter(
            SubType.code.isnot(None),
            SubType.code != '',
            SubType.code.notin_(['I24', 'TICKET_INT'])  # Escludi servizi interni
        ).all()
        
        # Crea mapping dinamico: nome_servizio_lowercase -> codice
        mapping = {}
        for service in db_services:
            if service.name and service.code:
                # Aggiungi il nome esatto
                mapping[service.name.lower().strip()] = service.code
                
                # Aggiungi varianti comuni per compatibilità
                name_lower = service.name.lower().strip()
                if name_lower == "formazione 4.0":
                    mapping["formazione quattro punto zero"] = service.code
                    mapping["formazioni 4.0"] = service.code
                elif name_lower == "patent box":
                    mapping["patentbox"] = service.code
                elif name_lower == "know how":
                    mapping["knowhow"] = service.code
                elif name_lower == "bandi":
                    mapping["bando"] = service.code
                    mapping["incentivi"] = service.code
                elif name_lower == "finanziamenti":
                    mapping["finanziamento"] = service.code
        
        print(f"[DEBUG] Dynamic mapping generato: {mapping}")
        
    except Exception as e:
        print(f"[ERROR] Errore lettura mapping da DB: {e}")
        # Fallback al mapping hardcoded solo in caso di errore
        mapping = {
            "formazione 4.0": "F40",
            "transizione 5.0": "T50", 
            "know how": "KHW",
            "patent box": "PBX",
            "bandi": "BND",
            "finanziamenti": "FND"
        }
    finally:
        db.close()
    
    found = set()
    
    # Cerca nella descrizione
    if description:
        description = description.lower()
        for phrase, code in mapping.items():
            if phrase in description:
                found.add(code)
                print(f"[DEBUG] Trovato '{phrase}' -> {code} in descrizione")
    
    # Cerca nei servizi forniti
    if services:
        for label in services:
            if not label:
                continue
            label = label.lower().strip()
            print(f"[DEBUG] Checking service: '{label}'")
            
            # Exact match prima
            if label in mapping:
                found.add(mapping[label])
                print(f"[DEBUG] Exact match: '{label}' -> {mapping[label]}")
                continue
            
            # Partial match come fallback
            for phrase, code in mapping.items():
                if phrase in label or label in phrase:
                    found.add(code)
                    print(f"[DEBUG] Partial match: '{label}' contains '{phrase}' -> {code}")
                    break
    
    result = list(found)
    print(f"[DEBUG] Final extracted codes: {result}")
    return result


def extract_services_from_description(description: str) -> list[str]:
    """
    Ritorna un elenco di etichette di servizi riconosciute a partire dalla descrizione.
    Ora usa il database dinamicamente.
    """
    from app.core.database import SessionLocal
    from app.models.sub_type import SubType
    
    # Get dynamic mapping from database
    db = SessionLocal()
    try:
        db_services = db.query(SubType).filter(
            SubType.code.isnot(None),
            SubType.code != '',
            SubType.code.notin_(['I24', 'TICKET_INT'])
        ).all()
        
        # Crea mapping: nome_lowercase -> nome_originale
        mapping = {}
        for service in db_services:
            if service.name:
                mapping[service.name.lower().strip()] = service.name
                
    except Exception as e:
        print(f"[ERROR] Errore lettura servizi da DB: {e}")
        # Fallback
        mapping = {
            "formazione 4.0": "Formazione 4.0",
            "transizione 5.0": "Transizione 5.0",
            "know how": "Know How", 
            "patent box": "Patent Box",
            "bandi": "Bandi",
            "finanziamenti": "Finanziamenti"
        }
    finally:
        db.close()
    
    found = set()
    if description:
        description = description.lower()
        for phrase, label in mapping.items():
            if phrase in description:
                found.add(label)
    
    return list(found)
