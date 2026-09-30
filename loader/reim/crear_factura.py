from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from models.comprobante import Comprobante
import config
from mappings.contenido import CONTENIDO_ES_EN


class CargaCabeceraError(Exception):
    """Fallo al cargar el tab 'Ingreso de Factura'."""
    pass


# Prefijo comun de todos los campos del tab "Ingreso de Factura".
# El indice ':2:' puede variar segun la instancia; si cambia, ajustar aca.
PREFIJO = "pt1:contentAreaReg:0:tabrg2:2:"

# Sufijos de los campos del tab Ingreso de Factura.
# Se usan con selector por sufijo (name$=...) porque el indice tabrgN
# cambia con cada documento creado (tabrg2, tabrg3, ...).
CAMPOS = {
    "cod_doc_fiscal":   "soc10",
    "contenido":        "soc12",
    "fecha_documento":  "id6",
    "nro_factura":      "it6",
    "letra":            "it7",
    "nro_cae":          "it8",
    "venc_cae":         "it9",
    "importe_total":    "it10",
    "neto_gravado":     "it2",
    "neto_no_gravado":  "it4",
    "id_bpm":           "it11",
}

class CrearFactura:
    """
    Llena el tab 'Ingreso de Factura' con los datos del Comprobante.
    Requiere que proveedor + OC ya esten cargados (campos habilitados).
    """

    def __init__(self, page: Page):
        self.page = page

    # ---------- Helpers ----------
    def _input(self, clave: str):
        sufijo = CAMPOS[clave]
        # Sufijo simple + filtro VISIBLE. Los indices del name (tabrgN y el
        # del medio) cambian con cada documento; el unico visible es el del
        # tab activo. Esto resuelve tambien la colision de 'it2'.
        return self.page.locator(
            f'input[name$="{sufijo}"]:visible'
        ).first

    def _select(self, clave: str):
        sufijo = CAMPOS[clave]
        return self.page.locator(
            f'select[name$="{sufijo}"]:visible'
        ).first

    def _llenar_input(self, clave: str, valor: str):
        campo = self._input(clave)
        campo.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)
        campo.click()
        campo.fill("")          # limpiar por si trae valor previo
        campo.fill(str(valor))
        campo.press("Tab")      # dispara validacion/reformateo de ADF


    def _seleccionar_combo(self, clave: str, texto_visible: str):
        """
        Selecciona una opcion del combo ADF escribiendo el texto (filtra) +
        Enter + Tab. Si el texto esperado no esta en las opciones (ej. el combo
        contenido a veces esta en ingles), usa el equivalente bilingue.
        """
        combo = self._select(clave)
        combo.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)

        # Opciones reales del combo
        opciones = combo.evaluate(
            "el => [...el.options].map(o => o.text)"
        )

        # Determinar el texto a escribir: el esperado, o su equivalente EN
        texto_a_usar = texto_visible
        if texto_visible not in opciones:
            equivalente = CONTENIDO_ES_EN.get(texto_visible)
            if equivalente and equivalente in opciones:
                texto_a_usar = equivalente
            else:
                raise CargaCabeceraError(
                    f"Combo '{clave}': '{texto_visible}' no esta en las "
                    f"opciones {opciones} ni su equivalente."
                )

        # Escribir + seleccionar (tecnica ADF)
        combo.click()
        combo.type(texto_a_usar)
        self.page.wait_for_timeout(400)
        combo.press("Enter")
        self.page.wait_for_timeout(300)
        combo.press("Tab")
        self.page.wait_for_timeout(300)

        # Verificar (contra el texto que efectivamente usamos)
        seleccionado = combo.evaluate(
            "el => el.options[el.selectedIndex]?.text || ''"
        )
        if seleccionado.strip() != texto_a_usar.strip():
            raise CargaCabeceraError(
                f"Combo '{clave}': se esperaba '{texto_a_usar}' pero quedo "
                f"'{seleccionado}'."
            )

    # ---------- Flujo principal ----------
    def llenar(self, comp: Comprobante):
        """Llena todos los campos del tab Ingreso de Factura."""
        # Combos
        self._seleccionar_combo("cod_doc_fiscal", comp.cod_doc_fiscal)
        self._seleccionar_combo("contenido", comp.contenido_factura)

        # Fechas (se envian tal cual vienen del CSV; ADF reformatea)
        self._llenar_input("fecha_documento", comp.fecha_documento)
        self._llenar_input("venc_cae", comp.venc_cae)

        # Textos
        self._llenar_input("nro_factura", comp.nro_factura)
        self._llenar_input("letra", comp.letra)
        self._llenar_input("nro_cae", comp.nro_cae)
        self._llenar_input("id_bpm", comp.id_bpm)

        # Importes
        self._llenar_input("importe_total", comp.importe_total)

        # Neto: SIEMPRE se llenan ambos, aunque sean 0
        self._llenar_input("neto_gravado", comp.neto_gravado)
        self._llenar_input("neto_no_gravado", comp.neto_no_gravado)