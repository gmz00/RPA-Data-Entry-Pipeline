from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from models.comprobante import Comprobante, LineaImpuesto
import config
from reim.popups import cerrar_popup_error_si_existe


class DesgloseImpuestosError(Exception):
    """Fallo al cargar una linea de impuesto en el tab Desglose."""
    pass


# Indice del boton "+" (Agregar) por seccion
BOTON_AGREGAR = {"IVA": 0, "PERCEPCION": 1, "IMP_INTERNO": 2}


class DesgloseImpuestos:
    """
    Carga el tab 'Desglose de Impuesto': agrega cada linea de impuesto
    (via popup) y completa los montos. Ubica los inputs por codigo de
    impuesto para no depender del orden de las filas.
    """

    def __init__(self, page: Page):
        self.page = page

    # ---------- Navegacion ----------
    def ir_al_tab(self):
        """
        Cambia al tab Desglose. Si el popup de error aborta el cambio,
        lo cierra y reintenta (hasta 3 veces).
        """
        for intento in range(3):
            self.page.get_by_role("tab", name="Desglose de Impuesto").click()
            self.page.wait_for_timeout(1000)
            cerrar_popup_error_si_existe(self.page)

            # Verificar que realmente cambiamos de tab
            if self._esta_en_desglose():
                return

        raise DesgloseImpuestosError(
            "No se pudo cambiar al tab Desglose tras 3 intentos."
        )

    def _esta_en_desglose(self) -> bool:
        """Detecta si el tab Desglose esta activo (aparece la seccion IVA/Percepciones)."""
        try:
            # "Percepciones" solo existe en el tab Desglose
            return self.page.get_by_text("Percepciones", exact=True).first.is_visible()
        except Exception:
            return False

    # ---------- Helper: escribir monto con eventos ADF ----------
    def _escribir_monto(self, name_input: str, valor: float):
        """
        Escribe un monto en la celda de la grilla igual que un humano:
        click + fill + Tab. La tecnica de eventos JS no sirve aca: ADF
        re-renderiza la celda y pisa el valor con 0.
        """
        campo = self.page.locator(f'input[name="{name_input}"]')
        campo.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)
        campo.click()
        campo.fill("")
        campo.fill(str(valor))
        campo.press("Tab")
        self.page.wait_for_timeout(300)

    # ---------- Helper: obtener el 'name' de un input por codigo+columna ----------
    def _name_input_por_codigo(self, codigo: str, col_index: int) -> str:
        """
        Busca el input de la fila cuyo primer td contiene el codigo, en la
        columna col_index. Reintenta hasta que ADF termine de renderizar.
        """
        js = """(datos) => {
            const inputs = [...document.querySelectorAll('input[type="text"]')];
            for (const inp of inputs) {
                const tr = inp.closest('tr');
                if (!tr) continue;
                const primerTd = tr.querySelector('td');
                if (!primerTd) continue;
                if (!primerTd.textContent.includes(datos.codigo)) continue;
                const td = inp.closest('td');
                if (!td) continue;
                const idx = [...td.parentElement.children].indexOf(td);
                if (idx === datos.col) return inp.name;
            }
            return null;
        }"""

        # Reintentar hasta 20 veces (10s) esperando a que renderice la fila
        for _ in range(20):
            name = self.page.evaluate(js, {"codigo": codigo, "col": col_index})
            if name:
                return name
            self.page.wait_for_timeout(500)

        raise DesgloseImpuestosError(
            f"No se encontro input para codigo '{codigo}' col {col_index}"
        )

    # ---------- Agregar una linea via popup ----------
    def _agregar_linea(self, categoria: str, codigo: str):
        cerrar_popup_error_si_existe(self.page)
        idx = BOTON_AGREGAR[categoria]
        self.page.get_by_role("button", name="Agregar").nth(idx).click()
        
        # 2. Seleccionar la fila del codigo en el popup
        try:
            fila = self.page.get_by_role("gridcell", name=codigo, exact=True)
            fila.wait_for(state="visible", timeout=config.TIMEOUT_DEFAULT)
            fila.click()
        except PlaywrightTimeout:
            # Cerrar popup para no dejar la pantalla trabada
            self.page.get_by_role("button", name="Cancelar").first.click()
            raise DesgloseImpuestosError(
                f"Codigo '{codigo}' no encontrado en el popup de {categoria}. "
                f"Puede que ya este agregado o no exista."
            )

        # 3. Aceptar
        self.page.get_by_role("button", name="Aceptar").click()

        # 4. Esperar a que la fila aparezca en la grilla (input editable)
        self.page.wait_for_timeout(2000)  # esperar a que ADF renderice la fila

    # ---------- Cargar una LineaImpuesto completa ----------
    def _cargar_linea(self, linea: LineaImpuesto):
        # Agregar la linea (popup)
        self._agregar_linea(linea.tipo, linea.codigo_reim)

        # Llenar montos segun tipo
        if linea.tipo == "IVA":
            # Escribir Base (col 2), luego RE-buscar y escribir Importe (col 3).
            # Se re-busca el Importe DESPUES de la Base porque ADF re-renderiza
            # la fila al escribir la base y el name previo queda obsoleto.
            name_base = self._name_input_por_codigo(linea.codigo_reim, 2)
            self._escribir_monto(name_base, linea.base_imponible)
            self.page.wait_for_timeout(500)  # dejar que ADF procese la base
            name_imp = self._name_input_por_codigo(linea.codigo_reim, 3)
            self._escribir_monto(name_imp, linea.importe)
        else:
            # PERCEPCION / IMP_INTERNO: solo Importe (col 1)
            name_imp = self._name_input_por_codigo(linea.codigo_reim, 1)
            self._escribir_monto(name_imp, linea.importe)

    # ---------- Flujo principal ----------
    def cargar(self, comp: Comprobante):
        """Carga todas las lineas de impuesto del comprobante."""
        self.ir_al_tab()
        for linea in comp.lineas_impuesto:
            self._cargar_linea(linea)