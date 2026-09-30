"""
Configuración global del módulo extractor CLIENT_NAME
Contiene URLs, timeouts, rutas y constantes del sistema
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# RUTAS DEL PROYECTO
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
SRC_DIR = BASE_DIR / "src"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
TESTS_DIR = BASE_DIR / "tests"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# ARCHIVOS DE ENTRADA/SALIDA
# ============================================================================
IDS_FILE = BASE_DIR / "ids.txt"
OUTPUT_CSV = OUTPUT_DIR / "comprobantes.csv"
LOG_FILE = LOGS_DIR / "extractor.log"

# ============================================================================
# CREDENCIALES (desde .env)
# ============================================================================

load_dotenv()

CLIENT_NAME_USER = os.getenv("CLIENT_NAME_USER")
CLIENT_NAME_PASS = os.getenv("CLIENT_NAME_PASS")

# ============================================================================
# URLs DEL PORTAL CLIENT_NAME
# ============================================================================
# Definir PORTAL_BASE_URL en .env  (debe incluir el esquema, ej: https://portal.example.com)
BASE_URL = os.getenv("PORTAL_BASE_URL", "https://portal-operativo.example.com")
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/TENANT_NAME/home"


def get_comprobante_url(id_comprobante: int) -> str:
    """Genera URL de un comprobante específico"""
    return f"{BASE_URL}/TENANT_NAME/rcp/receiptsAnalysis/{id_comprobante}"


# ============================================================================
# CONFIGURACIÓN DE PLAYWRIGHT
# ============================================================================
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))  # 30 segundos
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
SLOW_MO = 0 if HEADLESS else 100  # Ralentizar en modo visual para debug

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# CONSTANTES DE NEGOCIO
# ============================================================================
# Valores por defecto para campos opcionales
DEFAULT_TIPO_CONTENIDO = "Otros/Mercadería"

# Pestañas del comprobante (orden de extracción)
PESTANAS = ["CABECERA", "IMPORTES", "RECEPCIONES"]

# Estados de extracción posibles
ESTADO_OK = "OK"
ESTADO_ERROR_CABECERA = "ERROR_CABECERA"
ESTADO_ERROR_IMPORTES = "ERROR_IMPORTES"
ESTADO_ERROR_RECEPCIONES = "ERROR_RECEPCIONES"
ESTADO_SKIP = "SKIP"

# ============================================================================
# ESTRUCTURA DEL CSV (orden de columnas)
# ============================================================================
CSV_COLUMNS = [
    # CABECERA (8)
    "id",
    "emisor",
    "tipo",
    "nro_comprobante",
    "fecha_emision",
    "cae",
    "vencimiento_cae",
    "tipo_contenido",
    # IMPORTES (3)
    "neto_gravado",
    "no_gravado",
    "importe_total",
    # IMPUESTOS (39)
    # IVA (2)
    "imp_IVA_21",
    "imp_IVA_10_5",
    # Percepciones IIBB (24)
    "imp_PERC_IIBB_CABA",
    "imp_PERC_IIBB_BA",
    "imp_PERC_IIBB_CATAMARCA",
    "imp_PERC_IIBB_CHACO",
    "imp_PERC_IIBB_CHUBUT",
    "imp_PERC_IIBB_CORDOBA",
    "imp_PERC_IIBB_CORRIENTES",
    "imp_PERC_IIBB_ENTRE_RIOS",
    "imp_PERC_IIBB_FORMOSA",
    "imp_PERC_IIBB_JUJUY",
    "imp_PERC_IIBB_LA_PAMPA",
    "imp_PERC_IIBB_LA_RIOJA",
    "imp_PERC_IIBB_MENDOZA",
    "imp_PERC_IIBB_MISIONES",
    "imp_PERC_IIBB_NEUQUEN",
    "imp_PERC_IIBB_RIO_NEGRO",
    "imp_PERC_IIBB_SALTA",
    "imp_PERC_IIBB_SAN_JUAN",
    "imp_PERC_IIBB_SAN_LUIS",
    "imp_PERC_IIBB_SANTA_CRUZ",
    "imp_PERC_IIBB_SANTA_FE",
    "imp_PERC_IIBB_SGO_ESTERO",
    "imp_PERC_IIBB_TDF",
    "imp_PERC_IIBB_TUCUMAN",
    # Percepción IVA
    "imp_PERC_IVA_RG5329",
    # TSH (10) - IMPORTANTE: imp_TSH_SALTA agregado
    "imp_TSH_SALTA",
    "imp_TSH_TUCUMAN_TEM",
    "imp_TSH_TUCUMAN_TPP",
    "imp_TSH_CORRIENTES",
    "imp_TSH_COMODORO",
    "imp_TSH_CATAMARCA",
    "imp_TSH_CORDOBA",
    "imp_TSH_LA_PLATA",
    "imp_TSH_POSADAS",
    "imp_TSH_GENERICA",
    # Otros impuestos (2)
    "imp_INTERNO_LOCAL",
    "imp_OTROS",
    # RECEPCIONES (2)
    "nro_recepcion",
    "nro_oc",
    # CONTROL (2)
    "estado_extraccion",
    "motivo_error",
]


# ============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================
def validar_configuracion():
    """Valida que todos los requisitos estén cumplidos"""
    errores = []

    if not IDS_FILE.exists():
        errores.append(f"[ERROR] Archivo {IDS_FILE} no existe")

    if not CLIENT_NAME_USER or not CLIENT_NAME_PASS:
        errores.append("[ERROR] Credenciales incompletas en .env")

    if errores:
        raise ValueError("\n".join(errores))

    print("[OK] Configuracion validada correctamente")


if __name__ == "__main__":
    # Test de configuración
    validar_configuracion()
    print(f"[>>] Base DIR: {BASE_DIR}")
    print(f"[>>] Usuario CLIENT_NAME: {CLIENT_NAME_USER}")
    print(f"[>>] Login URL: {LOGIN_URL}")
    print(f"[>>] IDs file: {IDS_FILE}")
    print(f"[>>] Output CSV: {OUTPUT_CSV}")
