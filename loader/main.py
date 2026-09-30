import sys

from reim.session import ReimSession
from reim.buscador import Buscador, OCNoValidaError, ProveedorNoEncontradoError
from reim.crear_factura import CrearFactura, CargaCabeceraError
from reim.desglose_impuestos import DesgloseImpuestos, DesgloseImpuestosError
from reim.aprobar import (
    Aprobar, IvaMalCalculadoError, MontosNoCoincidenError, AprobacionError
)
from reim.popups import cerrar_popup_error_si_existe
from reader.csv_reader import leer_comprobantes
from logger.logger import ResultadoLogger
import config


# Cada cuantos documentos procesados se reinicia el navegador.
# REIM acumula documentos en el DOM y rompe los selectores; reiniciar limpia todo.
REINICIAR_CADA = 10


def procesar_comprobante(page, comp, log):
    """
    Carga un comprobante completo en REIM.
    Devuelve True si se proceso OK, False si fallo (ya registrado en el log).
    """
    b = Buscador(page)
    cf = CrearFactura(page)
    di = DesgloseImpuestos(page)
    ap = Aprobar(page)

    try:
        b.cargar_proveedor_y_oc(comp.nombre_proveedor, comp.nro_oc)
        cf.llenar(comp)
        di.cargar(comp)
        ap.aprobar()
        log.registrar_procesado(comp)
        return True

    except OCNoValidaError as e:
        log.registrar_fallido(comp, str(e), etapa="OC")
    except ProveedorNoEncontradoError as e:
        log.registrar_fallido(comp, str(e), etapa="Proveedor")
    except CargaCabeceraError as e:
        log.registrar_fallido(comp, str(e), etapa="Cabecera")
    except DesgloseImpuestosError as e:
        log.registrar_fallido(comp, str(e), etapa="Desglose")
    except IvaMalCalculadoError as e:
        log.registrar_fallido(comp, str(e), etapa="IVA_mal_calculado")
    except MontosNoCoincidenError as e:
        log.registrar_fallido(comp, str(e), etapa="montos_no_coinciden")
    except AprobacionError as e:
        log.registrar_fallido(comp, str(e), etapa="Aprobacion")
    except Exception as e:
        log.registrar_fallido(comp, f"Error inesperado: {e}", etapa="Desconocido")

    return False


def volver_a_busqueda(s, log, id_bpm) -> bool:
    """
    Vuelve a 'Busqueda de documento' con el boton Cancelar.
    NO usa el menu Tareas. Reintenta cerrando popups/menus con Esc.
    Devuelve True si lo logro.
    """
    for intento in range(3):
        try:
            cerrar_popup_error_si_existe(s.page)
            s.page.keyboard.press("Escape")
            s.page.wait_for_timeout(300)

            s.page.get_by_role("button", name="Cancelar").click(timeout=5000)
            s.page.get_by_text("Resultados", exact=True).wait_for(
                timeout=config.TIMEOUT_DEFAULT
            )
            return True
        except Exception as e:
            log.warning(f"Intento {intento+1} de volver a Busqueda fallo "
                        f"(id={id_bpm}): {e}")
            s.page.keyboard.press("Escape")
            s.page.wait_for_timeout(500)
    return False


def abrir_sesion(log):
    """Abre navegador + login + navega a Busqueda de documento. Devuelve la sesion."""
    s = ReimSession(headless=False)
    s.iniciar()
    s.login()
    s.ir_a_busqueda_documento()
    log.info("Sesion REIM iniciada.")
    return s


def cerrar_sesion(s, log):
    """Cierra la sesion/navegador de forma segura."""
    try:
        s.cerrar()
        log.info("Sesion REIM cerrada.")
    except Exception as e:
        log.warning(f"Error al cerrar sesion: {e}")


def _validar_credenciales():
    """Verifica que las variables de entorno de REIM estén presentes antes de abrir el navegador."""
    faltantes = [
        nombre
        for nombre, valor in [
            ("REIM_URL",      config.REIM_URL),
            ("REIM_USER",     config.REIM_USER),
            ("REIM_PASSWORD", config.REIM_PASSWORD),
        ]
        if not valor
    ]
    if faltantes:
        print(f"[ERROR] Faltan las siguientes credenciales en .env: {', '.join(faltantes)}")
        sys.exit(1)


def main():
    _validar_credenciales()

    log = ResultadoLogger(output_dir="output")

    # 1. Leer CSV
    comps = leer_comprobantes(config.CSV_INPUT_PATH)
    log.info(f"Leidos {len(comps)} comprobantes del CSV")

    # 2. Reanudacion: saltear los ya procesados con exito
    ya_procesados = log.ids_ya_procesados()
    if ya_procesados:
        log.info(f"Ya procesados previamente (se saltean): {len(ya_procesados)}")

    # 3. Sesion REIM (se reinicia cada REINICIAR_CADA documentos)
    s = abrir_sesion(log)
    procesados_en_sesion = 0

    try:
        for comp in comps:
            # Saltear los ya procesados con exito
            if comp.id_bpm in ya_procesados:
                log.info(f"SALTEADO (ya procesado): id={comp.id_bpm}")
                continue

            # Fallido en el reader (mapeo, etc.): no tocar REIM
            if comp.estado == "fallido":
                log.registrar_fallido(comp, comp.motivo_error, etapa="Reader")
                continue

            # Sin OC: no se puede procesar en REIM
            if not comp.nro_oc.strip():
                log.registrar_fallido(comp, "Comprobante sin numero de OC",
                                      etapa="sin_OC")
                continue

            # Reinicio preventivo cada REINICIAR_CADA documentos procesados
            if procesados_en_sesion >= REINICIAR_CADA:
                log.info(f"Reinicio preventivo tras {procesados_en_sesion} "
                         f"documentos (limpiar DOM de REIM).")
                cerrar_sesion(s, log)
                s = abrir_sesion(log)
                procesados_en_sesion = 0

            log.info(f"--- Procesando id={comp.id_bpm} ({comp.nombre_proveedor}) ---")

            # Crear nuevo documento
            try:
                cerrar_popup_error_si_existe(s.page)
                s.crear_nuevo_documento()
            except Exception as e:
                log.registrar_fallido(comp, f"No se pudo crear documento: {e}",
                                      etapa="CrearDoc")
                # Pantalla puede estar rara -> reiniciar sesion
                cerrar_sesion(s, log)
                s = abrir_sesion(log)
                procesados_en_sesion = 0
                continue

            # Procesar el comprobante
            ok = procesar_comprobante(s.page, comp, log)
            procesados_en_sesion += 1  # cuenta intentos en REIM (ok o fallido)

            # Volver a Busqueda de documento para el proximo
            if not volver_a_busqueda(s, log, comp.id_bpm):
                # Si no se pudo volver, reiniciar sesion (mas robusto que abortar)
                log.warning("No se pudo volver a Busqueda. Reiniciando sesion.")
                cerrar_sesion(s, log)
                s = abrir_sesion(log)
                procesados_en_sesion = 0

    finally:
        cerrar_sesion(s, log)

    # 4. Resumen final
    log.resumen()


if __name__ == "__main__":
    main()