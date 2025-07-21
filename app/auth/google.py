from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt, jwk
from jose.utils import base64url_decode
import os
import requests
from app.models.owner import Owner
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

from fastapi.responses import JSONResponse

@router.get("/login")
async def login(request: Request):
    next_url = request.query_params.get("next", "/dashboard")
    return JSONResponse(
        content={"status": "🟢 fake login disabilitato", "next": next_url}
    )

@router.get("/callback")
async def auth_callback(request: Request):
    # Stateless fallback: salta validazione CSRF state
    params = dict(request.query_params)
    if "state" not in params:
        params["state"] = "/dashboard"
    token = await oauth.google.fetch_access_token(
        str(request.url_for("auth_callback")),

        authorization_response=str(request.url),
        **params
    )

    jwt_token = token.get("id_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="ID token non fornito da Google")

    next_url = request.query_params.get("state", "/dashboard")

    html = f"""
    <html>
      <head>
        <script>
          localStorage.setItem("google_token", "{jwt_token}");
          window.location.href = decodeURIComponent("{next_url}");
        </script>
      </head>
      <body>Redirecting...</body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> Owner:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token mancante o malformato")

    token = authorization.split(" ")[1]

    try:
        res = requests.get("https://www.googleapis.com/oauth2/v3/certs")
        res.raise_for_status()
        jwks = res.json()

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if not key:
            raise HTTPException(status_code=401, detail="Chiave pubblica Google non trovata")

        public_key = jwk.construct(key, algorithm="RS256")
        message, encoded_sig = token.rsplit('.', 1)
        decoded_sig = base64url_decode(encoded_sig.encode())

        if not public_key.verify(message.encode(), decoded_sig):
            raise HTTPException(status_code=401, detail="Firma non valida")

        payload = jwt.get_unverified_claims(token)
        if payload.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Audience non valida")

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email non trovata nel token")

        owner = db.query(Owner).filter(Owner.email == email).first()
        if not owner:
            raise HTTPException(status_code=403, detail="Utente non autorizzato")

        return owner

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token non valido: {str(e)}")
