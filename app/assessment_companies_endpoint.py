# AGGIUNGI QUESTO AL ROUTER ASSESSMENT

@router.get("/companies")
async def get_assessment_companies(search: str = "", db: Session = Depends(get_db)):
    """Get companies per assessment con ricerca"""
    try:
        query = """
        SELECT id, ragione_sociale, partita_iva, settore, dimensione_aziendale, numero_dipendenti
        FROM assessment_companies 
        WHERE ragione_sociale ILIKE %s OR partita_iva ILIKE %s
        ORDER BY ragione_sociale
        LIMIT 50
        """
        
        search_term = f"%{search}%"
        result = db.execute(text(query), (search_term, search_term))
        
        companies = []
        for row in result:
            companies.append({
                "id": row[0],
                "ragione_sociale": row[1], 
                "partita_iva": row[2],
                "settore": row[3],
                "dimensione_aziendale": row[4],
                "numero_dipendenti": row[5]
            })
            
        return {"companies": companies, "count": len(companies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")

@router.post("/companies")
async def create_assessment_company(company_data: dict, db: Session = Depends(get_db)):
    """Crea nuova azienda per assessment"""
    try:
        query = """
        INSERT INTO assessment_companies 
        (ragione_sociale, partita_iva, settore, dimensione_aziendale, numero_dipendenti, 
         fatturato_annuo, provincia, regione, sito_web, email_contatto, telefono, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        result = db.execute(text(query), (
            company_data.get("ragione_sociale"),
            company_data.get("partita_iva"), 
            company_data.get("settore"),
            company_data.get("dimensione_aziendale"),
            company_data.get("numero_dipendenti"),
            company_data.get("fatturato_annuo"),
            company_data.get("provincia"),
            company_data.get("regione"),
            company_data.get("sito_web"),
            company_data.get("email_contatto"),
            company_data.get("telefono"),
            company_data.get("note")
        ))
        
        company_id = result.fetchone()[0]
        db.commit()
        
        return {"success": True, "company_id": company_id, "message": "Azienda creata con successo"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore creazione azienda: {str(e)}")
