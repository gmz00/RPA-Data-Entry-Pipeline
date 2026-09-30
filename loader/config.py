import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Rutas base ---
# BASE_DIR = .../script/modulo2_oracle_loader
BASE_DIR = Path(__file__).resolve().parent
# SCRIPT_DIR = .../script  (directorio padre comun a modulo1 y modulo2)
SCRIPT_DIR = BASE_DIR.parent

# --- Conexión REIM ---
REIM_URL = os.getenv("REIM_URL")
REIM_USER = os.getenv("REIM_USER")
REIM_PASSWORD = os.getenv("REIM_PASSWORD")

# --- Rutas de archivos ---
# CSV de entrada: lo genera el modulo 1
CSV_INPUT_PATH = os.getenv(
    "CSV_INPUT_PATH",
    str(SCRIPT_DIR / "modulo1_extractor_CLIENT_NAME" / "output" / "comprobantes.csv"),
)
# Salidas del modulo 2 (dentro de este proyecto)
PROCESADOS_PATH = str(BASE_DIR / "output" / "procesados.csv")
FALLIDOS_PATH = str(BASE_DIR / "output" / "fallidos.csv")

# --- Timeouts (ms) ---
TIMEOUT_DEFAULT = int(os.getenv("TIMEOUT_DEFAULT", 20000))
TIMEOUT_CREAR_FACTURA = int(os.getenv("TIMEOUT_CREAR_FACTURA", 25000))

# --- Reglas de negocio ---
TOLERANCIA_MAXIMA = float(os.getenv("TOLERANCIA_MAXIMA", 100))
CODIGOS_FISCALES_VALIDOS = [
    "001_FACTURAS_A",
    "201_FACTURA_DE_CREDITO_ELECTRONICA_MIPYMES_(FCE)_A",
]