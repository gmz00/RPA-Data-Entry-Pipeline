"""
Script principal - Orquestador del extractor CLIENT_NAME
Lee IDs, extrae comprobantes, parsea y escribe CSV
"""

import logging
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent))

from config import settings
from src.scraper import CLIENT_NAMEScraper
from src.extractor import CLIENT_NAMEExtractor
from src.parser import parsear_a_fila_csv
from src.csv_handler import CSVHandler

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def leer_ids_archivo() -> List[int]:
    """
    Lee los IDs de comprobantes desde ids.txt

    Returns:
        list: IDs a procesar
    """
    try:
        if not settings.IDS_FILE.exists():
            logger.error(f"[ERROR] Archivo {settings.IDS_FILE} no existe")
            return []

        with open(settings.IDS_FILE, "r", encoding="utf-8-sig") as f:
            ids = []
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):  # Ignorar comentarios
                    try:
                        ids.append(int(linea))
                    except ValueError:
                        logger.warning(f"[WARN] ID invalido ignorado: {linea}")

        logger.info(f"[INFO] Leidos {len(ids)} IDs desde {settings.IDS_FILE}")
        return ids

    except Exception as e:
        logger.error(f"[ERROR] Error leyendo IDs: {e}")
        return []


def main():
    """Función principal del extractor"""

    print("\n" + "=" * 70)
    print("  EXTRACTOR CLIENT_NAME - Módulo 1: Comprobantes a CSV")
    print("=" * 70)

    # 1. Validar configuración
    try:
        settings.validar_configuracion()
    except ValueError as e:
        logger.error(f"[ERROR] Error de configuracion:\n{e}")
        return 1

    # 2. Leer IDs
    ids_totales = leer_ids_archivo()
    if not ids_totales:
        logger.error("[ERROR] No hay IDs para procesar")
        return 1

    # 3. Inicializar CSV Handler
    csv_handler = CSVHandler()
    csv_handler.inicializar_csv()

    # 4. Filtrar IDs ya procesados (opcional - para reintentos)
    ids_procesados = csv_handler.leer_ids_procesados()
    ids_pendientes = [id_ for id_ in ids_totales if id_ not in ids_procesados]

    if not ids_pendientes:
        logger.info("[OK] Todos los IDs ya fueron procesados")
        ids_pendientes = ids_totales  # Procesar todos de nuevo
    else:
        logger.info(
            f"[INFO] IDs pendientes: {len(ids_pendientes)}/{len(ids_totales)} (ya procesados: {len(ids_procesados)})"
        )

    # 5. Inicializar Scraper
    scraper = CLIENT_NAMEScraper(headless=settings.HEADLESS, slow_mo=settings.SLOW_MO)

    try:
        scraper.iniciar_navegador()

        # 6. Login
        if not scraper.login():
            logger.error("[ERROR] Login fallo - Abortando")
            return 1

        logger.info("[OK] Login exitoso - Iniciando extraccion\n")

        # 7. Inicializar Extractor
        extractor = CLIENT_NAMEExtractor(scraper)

        # 8. Procesar cada ID
        exitos = 0
        errores = 0

        for i, id_comp in enumerate(ids_pendientes, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"  [{i}/{len(ids_pendientes)}] Procesando ID: {id_comp}")
            logger.info(f"{'=' * 70}")

            try:
                # Extraer datos crudos
                datos_crudos = extractor.extraer_todo(id_comp)

                # Parsear a formato CSV
                fila_csv = parsear_a_fila_csv(datos_crudos)

                # Escribir en CSV
                if csv_handler.agregar_fila(fila_csv):
                    if fila_csv["estado_extraccion"] == settings.ESTADO_OK:
                        exitos += 1
                        logger.info(f"[OK] [{i}/{len(ids_pendientes)}] OK: {id_comp}")
                    else:
                        errores += 1
                        logger.warning(
                            f"[WARN] [{i}/{len(ids_pendientes)}] Con errores: {id_comp} | {fila_csv['motivo_error']}"
                        )
                else:
                    errores += 1
                    logger.error(
                        f"[ERROR] [{i}/{len(ids_pendientes)}] Fallo escritura CSV: {id_comp}"
                    )

            except Exception as e:
                errores += 1
                logger.error(
                    f"[ERROR] [{i}/{len(ids_pendientes)}] Error procesando {id_comp}: {e}"
                )

                # Escribir fila con error en CSV
                fila_error = {col: "" for col in settings.CSV_COLUMNS}
                for col in settings.CSV_COLUMNS:
                    if col.startswith("imp_") or col in [
                        "neto_gravado",
                        "no_gravado",
                        "importe_total",
                    ]:
                        fila_error[col] = 0

                fila_error["id"] = id_comp
                fila_error["estado_extraccion"] = "ERROR_GENERAL"
                fila_error["motivo_error"] = str(e)[:200]
                csv_handler.agregar_fila(fila_error)

        # 9. Resumen final
        print("\n" + "=" * 70)
        print("  RESUMEN FINAL")
        print("=" * 70)
        print(f"  Total procesados: {len(ids_pendientes)}")
        print(f"  [OK]  Exitosos:      {exitos}")
        print(f"  [!!]  Con errores:   {errores}")
        print(f"  [>>]  Tasa exito:    {exitos / len(ids_pendientes) * 100:.1f}%")
        print(f"\n  [>>]  CSV generado: {csv_handler.ruta_csv}")

        # Estadísticas del CSV
        stats = csv_handler.obtener_estadisticas()
        print(f"\n  [>>]  Estadisticas CSV:")
        print(f"     Total filas:        {stats.get('total', 0)}")
        print(f"     OK:                 {stats.get('ok', 0)}")
        print(f"     Error CABECERA:     {stats.get('error_cabecera', 0)}")
        print(f"     Error IMPORTES:     {stats.get('error_importes', 0)}")
        print(f"     Error RECEPCIONES:  {stats.get('error_recepciones', 0)}")
        print("=" * 70 + "\n")

        logger.info("[OK] Extraccion completada")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n[WARN] Extraccion interrumpida por el usuario")
        print("\n[!!] Proceso detenido. Cerrando navegador...")
        return 130

    except Exception as e:
        logger.error(f"[ERROR] Error fatal: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        scraper.cerrar()


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)

    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n[!!] Interrumpido por el usuario")
        exit_code = 130
    sys.exit(exit_code)
