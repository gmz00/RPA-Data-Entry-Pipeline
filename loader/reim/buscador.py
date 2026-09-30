from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
import config


class OCNoValidaError(Exception):
    """La OC no matchea con el proveedor (popup 'Valor no valido')."""
    pass


class ProveedorNoEncontradoError(Exception):
    """No aparecio la fila del proveedor en la busqueda por Razon Social."""
    pass


class Buscador:
    """
    Carga de Cabecera: busca proveedor por Razon Social e ingresa el N. de OC.
    La busqueda se hace SIEMPRE por nombre, nunca por codigo de proveedor [1].
    """

    def __init__(self, page: Page):
        self.page = page

    # ---------- Proveedor ----------
    def buscar_proveedor(self, nombre_proveedor: str):
        """
        Abre el popup de busqueda, ingresa la Razon Social y selecciona la fila
        con doble click (confirma sin necesidad de 'Aceptar').
        Lanza ProveedorNoEncontradoError si no aparece.
        """
        # 1. Abrir popup (lupa del campo Proveedor)
        self.page.get_by_label("Buscar: **Proveedor").click()

        # 2. Ingresar Razon Social (campo del CSV: emisor)
        campo = self.page.get_by_role("textbox", name="Nombre de proveedor")
        campo.wait_for(timeout=config.TIMEOUT_DEFAULT)
        campo.fill(nombre_proveedor)

        # 3. Buscar (boton DENTRO del popup)
        self.page.get_by_label("Buscar: Proveedor").get_by_role(
            "button", name="Buscar", exact=True
        ).click()

        # 4. Seleccionar la fila con DOBLE CLICK (confirma la seleccion en ADF)
        try:
            fila = self.page.get_by_role(
                "gridcell", name=nombre_proveedor, exact=True
            )
            fila.wait_for(timeout=config.TIMEOUT_DEFAULT)
            fila.dblclick()
        except PlaywrightTimeout:
            self._cerrar_popup_generico()
            raise ProveedorNoEncontradoError(
                f"Proveedor no encontrado por Razon Social: '{nombre_proveedor}'"
            )

        # 5. Verificar que el popup se cerro (el proveedor quedo cargado)
        try:
            self.page.get_by_role(
                "textbox", name="Nombre de proveedor"
            ).wait_for(state="hidden", timeout=config.TIMEOUT_DEFAULT)
        except PlaywrightTimeout:
            raise ProveedorNoEncontradoError(
                f"El popup de proveedor no se cerro tras seleccionar "
                f"'{nombre_proveedor}'. Revisar seleccion."
            )

    # ---------- Orden de Compra ----------
    _NAME_OC = "pt1:contentAreaReg:0:tabrg2:2:orderNo2Id"
    _NAME_DOC_FISCAL = "pt1:contentAreaReg:0:tabrg2:2:soc10"

    def ingresar_oc(self, nro_oc: str):
        """
        Escribe la OC disparando eventos input/change (ADF los necesita).
        Usa selector por SUFIJO 'orderNo2Id' porque el indice tabrgN cambia
        con cada documento creado (tabrg2, tabrg3, ...).
        """
        # Esperar a que el campo OC este visible (por sufijo, cualquier tabrgN)
        campo_oc = self.page.locator('input[name$="orderNo2Id"]').first
        campo_oc.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)

        # Escribir con la tecnica que ADF reconoce (input + change)
        self.page.evaluate(
            """(oc) => {
                const i = document.querySelector('input[name$="orderNo2Id"]');
                if (!i) throw new Error('Campo OC no encontrado');
                i.focus();
                i.value = oc;
                i.dispatchEvent(new Event('input', { bubbles: true }));
                i.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            str(nro_oc),
        )

        # Buscar
        self.page.get_by_role("button", name="Buscar", exact=True).click()

        # Verificar resultado
        self._verificar_resultado_oc(nro_oc)

    # Verificacion: el combo doc fiscal se habilita cuando la OC valida.
    def _verificar_resultado_oc(self, nro_oc: str):
        """
        La OC valido si el combo doc fiscal (sufijo soc10) VISIBLE se habilita.
        """
        try:
            self.page.wait_for_function(
                """() => {
                    const els = [...document.querySelectorAll('select[name$="soc10"]')];
                    const visible = els.find(e => e.offsetParent !== null);
                    return visible && !visible.disabled;
                }""",
                timeout=config.TIMEOUT_DEFAULT,
            )
        except PlaywrightTimeout:
            raise OCNoValidaError(
                f"OC '{nro_oc}': los campos no se habilitaron. "
                f"La OC no matchea con el proveedor o no existe."
            )

    # ---------- Helpers de popups ----------
    def _cerrar_popup_error(self):
        """
        Cierra el popup de Error. Principal: tecla Esc. Fallback: Aceptar / X.
        """
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
        except Exception:
            try:
                self.page.get_by_role("button", name="Aceptar").first.click(timeout=3000)
            except PlaywrightTimeout:
                self.page.get_by_role("link", name="Cerrar", exact=True).click()    

    def _cerrar_popup_generico(self):
        """Cierra un popup abierto (ej. busqueda de proveedor sin resultados)."""
        try:
            self.page.get_by_role("button", name="Cancelar").first.click(timeout=3000)
        except PlaywrightTimeout:
            pass

    # ---------- Orquestacion ----------
    def cargar_proveedor_y_oc(self, nombre_proveedor: str, nro_oc: str):
        """
        Paso completo de cabecera: proveedor + OC.
        Propaga las excepciones para que el orquestador (main) registre y
        se encargue de cancelar/volver. El buscador NO cancela (evita doble
        cancelacion con el main).
        """
        self.buscar_proveedor(nombre_proveedor)
        self.ingresar_oc(nro_oc)
