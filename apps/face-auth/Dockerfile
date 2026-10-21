FROM python:3.12-slim

# dépendances système pour face_recognition (dlib + cmake)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libopenblas-dev liblapack-dev \
    libx11-dev libgtk-3-dev libboost-python-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# setuptools<72 est nécessaire pour que pkg_resources soit disponible
# (setuptools 80+ supprime pkg_resources, requis par face_recognition_models)
# face_recognition_models doit venir de GitHub (la version PyPI ne contient pas les modèles)
RUN pip install --no-cache-dir "setuptools<72" && \
    pip install --no-cache-dir \
    git+https://github.com/ageitgey/face_recognition_models && \
    pip install --no-cache-dir -r requirements.txt

COPY face_auth/ ./face_auth/

# Dossier des visages connus (monté en volume)
RUN mkdir -p /app/known_faces

EXPOSE 8000

CMD ["uvicorn", "face_auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
