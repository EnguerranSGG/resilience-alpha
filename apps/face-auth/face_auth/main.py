"""
Service de reconnaissance faciale — RESILIENCE-ALPHA
Consigne Additionnelle 1 : MFA par caméra USB + ESP8266
"""

from __future__ import annotations

import base64
import io
import logging
import time
from pathlib import Path
from collections import defaultdict

import httpx
import numpy as np
import face_recognition
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from pydantic_settings import BaseSettings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    known_faces_dir: str = "/app/known_faces"
    esp_url: str = "http://192.168.137.2"   # IP de l'ESP8266 sur le hotspot
    max_attempts: int = 2
    lockout_seconds: int = 300              # 5 minutes
    tolerance: float = 0.5                  # seuil reconnaissance (plus bas = plus strict)

    model_config = {"env_prefix": "FACE_"}


settings = Settings()
app = FastAPI(title="face-auth", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Encodages des visages connus chargés au démarrage
known_encodings: dict[str, list] = {}
# Suivi des tentatives : {username: {"attempts": int, "locked_until": float}}
attempt_tracker: dict[str, dict] = defaultdict(lambda: {"attempts": 0, "locked_until": 0.0})


def load_known_faces():
    """Charge les encodages depuis known_faces/<username>/*.jpg"""
    faces_dir = Path(settings.known_faces_dir)
    if not faces_dir.exists():
        logger.warning("Dossier known_faces absent — aucun visage enregistré")
        return
    for user_dir in faces_dir.iterdir():
        if not user_dir.is_dir():
            continue
        encodings = []
        for img_path in user_dir.glob("*.jpg"):
            img = face_recognition.load_image_file(str(img_path))
            encs = face_recognition.face_encodings(img)
            if encs:
                encodings.append(encs[0])
        if encodings:
            known_encodings[user_dir.name] = encodings
            logger.info(f"Visage chargé : {user_dir.name} ({len(encodings)} image(s))")


def notify_esp(state: str):
    """Envoie l'état LED à l'ESP8266 via HTTP."""
    try:
        httpx.post(f"{settings.esp_url}/led", json={"state": state}, timeout=2.0)
    except Exception as e:
        logger.warning(f"ESP8266 injoignable : {e}")


def decode_image(b64_data: str) -> np.ndarray:
    """Décode une image base64 en tableau numpy RGB."""
    img_bytes = base64.b64decode(b64_data)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return np.array(img)


# ── Modèles Pydantic ────────────────────────────────────────────────────────

class VerifyRequest(BaseModel):
    username: str
    image_b64: str   # frame capturée par le navigateur (base64 JPEG/PNG)

class VerifyResponse(BaseModel):
    recognized: bool
    username: str
    message: str
    locked: bool = False
    locked_seconds: int = 0

class EnrollRequest(BaseModel):
    username: str
    image_b64: str

class LedRequest(BaseModel):
    state: str  # OFF | GREEN_BLINK | GREEN_SOLID | RED_BLINK | RED_SOLID


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    load_known_faces()
    notify_esp("OFF")


@app.get("/health")
def health():
    return {"status": "ok", "known_users": list(known_encodings.keys())}


@app.post("/face/verify", response_model=VerifyResponse)
def verify_face(req: VerifyRequest):
    """
    Étape 1 du login : vérifie que le visage correspond à l'identifiant.
    Gère le blocage après max_attempts échecs.
    """
    username = req.username.strip().lower()
    tracker = attempt_tracker[username]

    # Vérifier si bloqué
    if tracker["locked_until"] > time.time():
        remaining = int(tracker["locked_until"] - time.time())
        notify_esp("RED_SOLID")
        return VerifyResponse(
            recognized=False,
            username=username,
            message=f"Compte bloqué — réessayez dans {remaining}s",
            locked=True,
            locked_seconds=remaining,
        )

    # Décoder et analyser l'image
    try:
        frame = decode_image(req.image_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide")

    face_locations = face_recognition.face_locations(frame)
    if not face_locations:
        notify_esp("RED_SOLID")
        return VerifyResponse(recognized=False, username=username, message="Aucun visage détecté")

    face_encs = face_recognition.face_encodings(frame, face_locations)
    user_encs = known_encodings.get(username, [])

    recognized = False
    if user_encs and face_encs:
        results = face_recognition.compare_faces(user_encs, face_encs[0], tolerance=settings.tolerance)
        recognized = any(results)

    if recognized:
        tracker["attempts"] = 0
        notify_esp("GREEN_BLINK")
        logger.info(f"Visage reconnu : {username}")
        return VerifyResponse(recognized=True, username=username, message="Visage reconnu")
    else:
        tracker["attempts"] += 1
        logger.warning(f"Visage non reconnu : {username} (tentative {tracker['attempts']}/{settings.max_attempts})")
        if tracker["attempts"] >= settings.max_attempts:
            tracker["locked_until"] = time.time() + settings.lockout_seconds
            tracker["attempts"] = 0
            notify_esp("RED_SOLID")
            return VerifyResponse(
                recognized=False,
                username=username,
                message=f"Trop de tentatives — bloqué {settings.lockout_seconds}s",
                locked=True,
                locked_seconds=settings.lockout_seconds,
            )
        notify_esp("RED_SOLID")
        return VerifyResponse(recognized=False, username=username, message="Visage non reconnu")


@app.post("/face/password-ok")
def password_ok():
    """Appelé quand le MDP est validé → LED verte fixe 30s."""
    notify_esp("GREEN_SOLID")
    return {"status": "ok"}


@app.post("/face/password-fail")
def password_fail():
    """Appelé quand le MDP est refusé → LED rouge clignote 10x."""
    notify_esp("RED_BLINK")
    return {"status": "ok"}


@app.post("/esp/led")
def set_led(req: LedRequest):
    """Relais direct vers l'ESP8266 (utile pour les tests)."""
    notify_esp(req.state)
    return {"status": "sent", "state": req.state}


@app.post("/face/enroll")
def enroll(req: EnrollRequest):
    """Enregistre un nouveau visage pour un utilisateur (admin)."""
    username = req.username.strip().lower()
    try:
        frame = decode_image(req.image_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide")

    encs = face_recognition.face_encodings(frame)
    if not encs:
        raise HTTPException(status_code=422, detail="Aucun visage détecté dans l'image")

    user_dir = Path(settings.known_faces_dir) / username
    user_dir.mkdir(parents=True, exist_ok=True)
    idx = len(list(user_dir.glob("*.jpg")))
    out = user_dir / f"face_{idx:03d}.jpg"
    Image.fromarray(frame).save(str(out))

    if username not in known_encodings:
        known_encodings[username] = []
    known_encodings[username].append(encs[0])

    logger.info(f"Visage enregistré : {username} → {out}")
    return {"status": "enrolled", "username": username, "file": str(out)}
