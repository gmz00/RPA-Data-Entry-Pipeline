"""
Parseo de datos extraidos a formato CSV
Mapea impuestos a columnas especificas
"""

import logging
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from config.selectors import mapear_impuesto

logger = logging.getLogger(__name__)


def parsear_a_fila_csv(datos_crudos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte datos crudos de extractor a fila CSV con 47 columnas

    Args:
        datos_crudos: dict retornado por CLIENT_NAMEExtractor.extraer_todo()

    Returns:
        dict con todas las columnas de settings.CSV_COLUMNS
    """

    # Inicializar fila con valores por defecto
    fila = {col: "" for col in settings.CSV_COLUMNS}

    # Campos numericos a 0
    for col in settings.CSV_COLUMNS:
        if col.startswith("imp_") or col in [
            "neto_gravado",
            "no_gravado",
            "importe_total",
        ]:
            fila[col] = 0

    try:
        # ===== CABECERA =====
        fila["id"] = datos_crudos.get("id", "")
        fila["emisor"] = datos_crudos.get("emisor", "")
        fila["tipo"] = datos_crudos.get("tipo", "")
        fila["nro_comprobante"] = datos_crudos.get("nro_comprobante", "")
        fila["fecha_emision"] = datos_crudos.get("fecha_emision", "")
        fila["cae"] = datos_crudos.get("cae", "")
        fila["vencimiento_cae"] = datos_crudos.get("vencimiento_cae", "")
        fila["tipo_contenido"] = datos_crudos.get("tipo_contenido", "")

        # ===== IMPORTES =====
        fila["neto_gravado"] = datos_crudos.get("neto_gravado", 0)
        fila["no_gravado"] = datos_crudos.get("no_gravado", 0)
        fila["importe_total"] = datos_crudos.get("importe_total", 0)

        # ===== IMPUESTOS (mapeo de dict a columnas) =====
        impuestos_raw = datos_crudos.get("impuestos_raw", {})

        for descripcion_CLIENT_NAME, monto in impuestos_raw.items():
            columna_csv = mapear_impuesto(descripcion_CLIENT_NAME)

            if columna_csv:
                fila[columna_csv] = monto
                logger.debug(
                    f"  [PARSER] {descripcion_CLIENT_NAME} → {columna_csv}: ${monto:,.2f}"
                )
            else:
                # Impuesto no mapeado → sumar a OTROS
                fila["imp_OTROS"] += monto
                logger.warning(
                    f"  [!] Impuesto no mapeado: '{descripcion_CLIENT_NAME}' (${monto:,.2f}) → imp_OTROS"
                )

        # ===== RECEPCIONES =====
        fila["nro_recepcion"] = datos_crudos.get("nro_recepcion", "")
        fila["nro_oc"] = datos_crudos.get("nro_oc", "")

        # ===== CONTROL =====
        fila["estado_extraccion"] = datos_crudos.get("estado_extraccion", "")
        fila["motivo_error"] = datos_crudos.get("motivo_error", "")

        logger.info(
            f"[PARSER] Fila generada: ID {fila['id']}, {len([k for k, v in fila.items() if v not in ['', 0]])} campos con datos"
        )

        return fila

    except Exception as e:
        logger.error(f"[PARSER ERROR] {e}")
        fila["estado_extraccion"] = "ERROR_PARSER"
        fila["motivo_error"] = str(e)[:200]
        return fila


def validar_fila(fila: Dict[str, Any]) -> bool:
    """Valida que fila tenga estructura correcta"""
    if not fila.get("id"):
        logger.error("[VALIDACION] Falta ID")
        return False

    if len(fila) != len(settings.CSV_COLUMNS):
        logger.error(
            f"[VALIDACION] Fila tiene {len(fila)} columnas, esperadas {len(settings.CSV_COLUMNS)}"
        )
        return False

    return True


# ============================================================================
# PRUEBA
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
    )

    # Simular datos reales del extractor (comprobante 9999999)
    datos_test = {
        "id": 9999999,
        "emisor": "Proveedor de Prueba S.A.",
        "tipo": "001",
        "nro_comprobante": "0001-00000011",
        "fecha_emision": "16-07-2026",
        "cae": "1111111111111",
        "vencimiento_cae": "26-07-2026",
        "tipo_contenido": "Otros/Mercadería",
        "neto_gravado": 123123123.30,
        "no_gravado": 0.0,
        "importe_total": 1237191.62,
        "impuestos_raw": {
            "IVA 21": 208491.21,
            "AP Perc IIBB Salta": 1136.57,
            "Perc IIBB CABA": 4964.08,
            "AP Perc IIBB Mendoza": 9928.15,
            "Perc IIBB Cordoba": 2482.04,
            "Perc IIBB Buenos Aires": 17374.27,
        },
        "nro_recepcion": "111111",
        "nro_oc": "222222222",
        "estado_extraccion": "OK",
        "motivo_error": "",
    }

    print("=" * 60)
    print("TEST PARSER - Comprobante 9999999")
    print("=" * 60)

    fila_csv = parsear_a_fila_csv(datos_test)

    print(f"\n[OK] Columnas totales: {len(fila_csv)}")
    print(f"[OK] Validacion: {'OK' if validar_fila(fila_csv) else 'ERROR'}")

    print("\n--- CAMPOS CON DATOS ---")
    for key, val in fila_csv.items():
        if val not in ["", 0]:
            if isinstance(val, float):
                print(f"  {key}: ${val:,.2f}")
            else:
                print(f"  {key}: {val}")

    print("\n--- IMPUESTOS MAPEADOS ---")
    for col in settings.CSV_COLUMNS:
        if col.startswith("imp_") and fila_csv[col] > 0:
            print(f"  [OK] {col}: ${fila_csv[col]:,.2f}")

    if fila_csv["imp_OTROS"] > 0:
        print(
            f"\n  [WARN] imp_OTROS: ${fila_csv['imp_OTROS']:,.2f} (hay impuestos sin mapear)"
        )
