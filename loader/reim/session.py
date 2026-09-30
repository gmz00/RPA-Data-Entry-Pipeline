from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
import config


class ReimSession:
    """
    Maneja la sesion de Oracle REIM: login + navegacion hasta la pantalla
    de Busqueda de documento, lista para crear facturas.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self.page: Page = None

    # ---------- Ciclo de vida ----------
    def iniciar(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--ignore-certificate-errors"],
        )
        # Ignoramos validación TLS debido a certificados autofirmados en la intranet del cliente
        self._context = self._browser.new_context(ignore_https_errors=True)
        self.page = self._context.new_page()
        self.page.set_default_timeout(config.TIMEOUT_DEFAULT)

    def cerrar(self):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def __enter__(self):
        self.iniciar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()

    # ---------- Login ----------
    def login(self):
        login_url = config.REIM_URL.replace("/Home", "/Login")
        self.page.goto(login_url)

        self.page.get_by_label("Nombre de usuario").fill(config.REIM_USER)
        self.page.get_by_label("Contraseña").fill(config.REIM_PASSWORD)
        self.page.get_by_role("button", name="Conexión").click()

        try:
            self.page.wait_for_url("**/faces/Home", timeout=config.TIMEOUT_DEFAULT)
        except PlaywrightTimeout:
            raise RuntimeError(
                "Login fallido: no se llego a /faces/Home. "
                "Revisar credenciales o selectores del formulario."
            )

    # ---------- Navegacion a Busqueda de documento ----------
    def ir_a_busqueda_documento(self):
        """
        Tareas > Confrontacion de facturas (la que funciona) > Busqueda de documento [1].
        """
        # 1. Abrir menu Tareas
        self.page.get_by_role("link", name="Tareas").click()

        # 2. Segunda entrada valida "Confrontacion de facturas" (nth(2) segun Inspector)
        #    La primera de la lista no funciona; usamos la ocurrencia detectada.
        self.page.get_by_role("link", name="Confrontación de facturas").nth(2).click()

        # 3. Submenu: Busqueda de documento
        self.page.get_by_role("link", name="Búsqueda de documento").click()

        # 4. Verificar que cargo la pantalla (aparece la seccion "Resultados")
        try:
            self.page.get_by_text("Resultados", exact=True).wait_for(
                timeout=config.TIMEOUT_DEFAULT
            )
        except PlaywrightTimeout:
            raise RuntimeError(
                "No se cargo la pantalla 'Busqueda de documento'. "
                "Revisar selectores del menu Tareas."
            )

    # ---------- Crear nuevo documento ----------
    def crear_nuevo_documento(self):
        """
        En la seccion Resultados, click en el boton 'Crear' (hoja + estrella).
        Luego espera a que cargue el tab 'Crear Factura' (~15s de delay conocido).
        """
        self.page.get_by_role("button", name="Crear").click()

        try:
            # El tab "Crear factura" (rol tab, no texto suelto) confirma la carga.
            self.page.get_by_role("tab", name="Crear factura").first.wait_for(
                timeout=config.TIMEOUT_CREAR_FACTURA
            )
        except PlaywrightTimeout:
            raise RuntimeError(
                "No aparecio el tab 'Crear Factura' tras presionar Crear. "
                "Revisar el selector del boton Crear o aumentar TIMEOUT_CREAR_FACTURA."
            )


