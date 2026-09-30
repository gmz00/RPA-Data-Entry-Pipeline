"""
Manejo de escritura CSV
Escritura incremental con pandas, validacion de estructura
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config import settings

logger = logging.getLogger(__name__)


class CSVHandler:
    """Manejador de escritura CSV"""

    def __init__(self, ruta_csv: Path = None):
        """
        Inicializa el manejador CSV

        Args:
            ruta_csv: Path del archivo CSV (None = usar settings.OUTPUT_CSV)
        """
        self.ruta_csv = ruta_csv or settings.OUTPUT_CSV
        self.columnas = settings.CSV_COLUMNS
        logger.info(f"[CSV] Inicializado: {self.ruta_csv}")

    def inicializar_csv(self) -> bool:
        """
        Crea el CSV con encabezados si no existe

        Returns:
            bool: True si se creó, False si ya existía
        """
        try:
            if self.ruta_csv.exists():
                logger.info(f"[CSV] Archivo ya existe: {self.ruta_csv}")
                return False

            # Crear DataFrame vacío con columnas
            df = pd.DataFrame(columns=self.columnas)
            df.to_csv(self.ruta_csv, index=False, encoding="utf-8-sig")

            logger.info(f"[CSV] Archivo creado: {self.ruta_csv}")
            return True

        except Exception as e:
            logger.error(f"[CSV ERROR] No se pudo crear archivo: {e}")
            raise

    def agregar_fila(self, fila: Dict[str, Any]) -> bool:
        """
        Agrega una fila al CSV (modo append)

        Args:
            fila: dict con las 47 columnas de settings.CSV_COLUMNS

        Returns:
            bool: True si se agregó correctamente
        """
        try:
            # Validar estructura
            if not self._validar_estructura(fila):
                logger.error(f"[CSV] Fila inválida, no se agregará")
                return False

            # Convertir a DataFrame
            df_fila = pd.DataFrame([fila])

            # Verificar si el CSV existe
            if not self.ruta_csv.exists():
                logger.warning(f"[CSV] Archivo no existe, creando...")
                self.inicializar_csv()

            # Agregar fila (append mode)
            df_fila.to_csv(
                self.ruta_csv,
                mode="a",  # Append
                header=False,  # No escribir encabezados
                index=False,
                encoding="utf-8-sig",
            )

            logger.info(
                f"[CSV] Fila agregada: ID {fila.get('id', 'N/A')} | Estado: {fila.get('estado_extraccion', 'N/A')}"
            )
            return True

        except Exception as e:
            logger.error(f"[CSV ERROR] No se pudo agregar fila: {e}")
            return False

    def agregar_multiples(self, filas: List[Dict[str, Any]]) -> int:
        """
        Agrega múltiples filas al CSV

        Args:
            filas: Lista de dicts con estructura de fila CSV

        Returns:
            int: Cantidad de filas agregadas exitosamente
        """
        exitosas = 0

        for i, fila in enumerate(filas, 1):
            if self.agregar_fila(fila):
                exitosas += 1
            else:
                logger.warning(f"[CSV] Fila {i}/{len(filas)} falló")

        logger.info(f"[CSV] Agregadas {exitosas}/{len(filas)} filas")
        return exitosas

    def leer_ids_procesados(self) -> List[int]:
        """
        Lee los IDs ya procesados del CSV

        Returns:
            list: IDs de comprobantes ya extraídos
        """
        try:
            if not self.ruta_csv.exists():
                logger.debug("[CSV] Archivo no existe, no hay IDs procesados")
                return []

            df = pd.read_csv(self.ruta_csv, usecols=["id"], encoding="utf-8-sig")
            ids = df["id"].dropna().astype(int).tolist()

            logger.info(f"[CSV] Leídos {len(ids)} IDs procesados")
            return ids

        except Exception as e:
            logger.error(f"[CSV ERROR] No se pudieron leer IDs: {e}")
            return []

    def _validar_estructura(self, fila: Dict[str, Any]) -> bool:
        """
        Valida que la fila tenga todas las columnas requeridas

        Args:
            fila: dict con datos de la fila

        Returns:
            bool: True si es válida
        """
        # Verificar que tenga todas las columnas
        if set(fila.keys()) != set(self.columnas):
            faltantes = set(self.columnas) - set(fila.keys())
            extras = set(fila.keys()) - set(self.columnas)

            if faltantes:
                logger.error(f"[VALIDACION] Faltan columnas: {faltantes}")
            if extras:
                logger.error(f"[VALIDACION] Columnas extra: {extras}")

            return False

        # Verificar que tenga ID
        if not fila.get("id"):
            logger.error("[VALIDACION] Fila sin ID")
            return False

        return True

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del CSV

        Returns:
            dict: {total, ok, error_cabecera, error_importes, error_recepciones}
        """
        try:
            if not self.ruta_csv.exists():
                return {
                    "total": 0,
                    "ok": 0,
                    "error_cabecera": 0,
                    "error_importes": 0,
                    "error_recepciones": 0,
                }

            df = pd.read_csv(
                self.ruta_csv, usecols=["estado_extraccion"], encoding="utf-8-sig"
            )

            stats = {
                "total": len(df),
                "ok": (df["estado_extraccion"] == settings.ESTADO_OK).sum(),
                "error_cabecera": (
                    df["estado_extraccion"] == settings.ESTADO_ERROR_CABECERA
                ).sum(),
                "error_importes": (
                    df["estado_extraccion"] == settings.ESTADO_ERROR_IMPORTES
                ).sum(),
                "error_recepciones": (
                    df["estado_extraccion"] == settings.ESTADO_ERROR_RECEPCIONES
                ).sum(),
            }

            logger.info(
                f"[CSV STATS] Total: {stats['total']} | OK: {stats['ok']} | Errores: {stats['total'] - stats['ok']}"
            )
            return stats

        except Exception as e:
            logger.error(f"[CSV ERROR] No se pudieron obtener estadísticas: {e}")
            return {}


# ============================================================================
# PRUEBA
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format=settings.LOG_FORMAT, datefmt=settings.LOG_DATE_FORMAT
    )

    # Crear handler
    csv_handler = CSVHandler()

    print("=" * 60)
    print("TEST CSV HANDLER")
    print("=" * 60)

    # Crear CSV
    print("\n1. Inicializando CSV...")
    csv_handler.inicializar_csv()

    # Fila de prueba (comprobante 2089578)
    fila_test = {col: "" for col in settings.CSV_COLUMNS}
    fila_test.update(
        {
            "id": 9999999,
            "emisor": "VENDOR_TEST_SA",
            "tipo": "001",
            "nro_comprobante": "00001-00000001",
            "fecha_emision": "16-07-2026",
            "cae": "99999999999999",
            "vencimiento_cae": "26-07-2026",
            "tipo_contenido": "Otros/Mercadería",
            "neto_gravado": 992815.30,
            "no_gravado": 0.0,
            "importe_total": 1237191.62,
            "imp_IVA_21": 208491.21,
            "imp_PERC_IIBB_SALTA": 1136.57,
            "imp_PERC_IIBB_CABA": 4964.08,
            "imp_PERC_IIBB_MENDOZA": 9928.15,
            "imp_PERC_IIBB_CORDOBA": 2482.04,
            "imp_PERC_IIBB_BA": 17374.27,
            "nro_recepcion": "111111",
            "nro_oc": "9999999999",
            "estado_extraccion": "OK",
            "motivo_error": "",
        }
    )

    # Inicializar impuestos no usados en 0
    for col in settings.CSV_COLUMNS:
        if col.startswith("imp_") and col not in fila_test:
            fila_test[col] = 0

    print("\n2. Agregando fila de prueba...")
    csv_handler.agregar_fila(fila_test)

    print("\n3. Leyendo IDs procesados...")
    ids = csv_handler.leer_ids_procesados()
    print(f"   IDs en CSV: {ids}")

    print("\n4. Estadísticas...")
    stats = csv_handler.obtener_estadisticas()
    for key, val in stats.items():
        print(f"   {key}: {val}")

    print(f"\n[OK] CSV creado en: {csv_handler.ruta_csv}")
    print("   Abre el archivo para verificar formato\n")
