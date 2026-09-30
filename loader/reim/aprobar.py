from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from reim.popups import cerrar_popup_error_si_existe
import config


class AprobacionError(Exception):
    """Fallo generico al aprobar el comprobante."""
    pass


class IvaMalCalculadoError(Exception):
    """
    REIM rechazo el IVA por diferencia de centavos (la calculadora de REIM
    tiene un intervalo aceptado distinto al de la factura). Ajuste manual.
    """
    pass


class MontosNoCoincidenError(Exception):
    """
    El Total de Impuesto del desglose no coincide con el de Ingreso Factura
    (suma de impuestos + netos != importe total). Revision manual.
    """
    pass


# Textos de los popups (fragmentos estables capturados de REIM)
TEXTO_EXITO = "¡Aprobado con éxito!"
# Aparece en 2 variantes ("...incorrectos, revise..." y
# "...incorrectos en la tabla del IVA, revise..."); usamos el fragmento comun.
TEXTO_ERROR_IVA = "base imponible y del importe de impuesto están incorrectos"
# Error: el total del desglose no coincide con el total de la factura.
TEXTO_ERROR_MONTOS = "debe de ser igual al campo"


class Aprobar:
    """
    Presiona 'Aprobar' y verifica el resultado:
      - Exito -> cierra el popup de confirmacion.
      - Error de IVA -> lanza IvaMalCalculadoError.
      - Montos no coinciden -> lanza MontosNoCoincidenError.
      - Otro error -> lanza AprobacionError.
    """

    def __init__(self, page: Page):
        self.page = page

    def aprobar(self):
        # Cerrar popup random previo si quedo abierto
        cerrar_popup_error_si_existe(self.page)

        # Click en Aprobar
        self.page.get_by_role("button", name="Aprobar").click()

        # Esperar hasta 15s reintentando (el popup puede tardar unos segundos,
        # mas aun con muchos impuestos).
        for _ in range(30):  # 30 x 500ms = 15s
            if self._popup_visible(TEXTO_EXITO):
                self._cerrar_popup()
                return  # aprobado OK

            if self._popup_visible(TEXTO_ERROR_IVA):
                self._cerrar_popup()
                raise IvaMalCalculadoError(
                    "IVA mal calculado: REIM rechaza base/importe. "
                    "Ajustar manualmente."
                )

            if self._popup_visible(TEXTO_ERROR_MONTOS):
                self._cerrar_popup()
                raise MontosNoCoincidenError(
                    "Total de impuesto no coincide con el total de la factura. "
                    "Revisar montos manualmente."
                )

            self.page.wait_for_timeout(500)

        # Timeout: ningun popup conocido
        if cerrar_popup_error_si_existe(self.page):
            raise AprobacionError(
                "Aprobacion fallida: aparecio un popup de error inesperado."
            )
        raise AprobacionError(
            "Aprobacion sin confirmacion tras 15s: no aparecio el cartel de "
            "exito ni un error conocido. Revisar manualmente."
        )

    # ---------- Helpers ----------
    def _popup_visible(self, texto: str) -> bool:
        try:
            loc = self.page.get_by_text(texto, exact=False)
            return loc.count() > 0 and loc.first.is_visible()
        except Exception:
            return False

    def _cerrar_popup(self):
        """Cierra el popup de resultado (Aceptar / Esc)."""
        try:
            self.page.get_by_role("button", name="Aceptar").first.click(timeout=3000)
        except PlaywrightTimeout:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)